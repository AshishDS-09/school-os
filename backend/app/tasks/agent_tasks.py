# backend/app/tasks/agent_tasks.py

import asyncio
import logging

from app.tasks import celery_app
from celery.schedules import crontab

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# EVENT-TRIGGERED TASKS  — run instantly via subscriber.py
# ══════════════════════════════════════════════════════════════════════

@celery_app.task(name="run_academic_agent_for_student", bind=True, max_retries=3)
def run_academic_agent_for_student(self, student_id: int, school_id: int):
    """Triggered by marks.entered event."""
    try:
        logger.info(
            f"[AcademicAgent] Starting for school_id={school_id} "
            f"student_id={student_id}"
        )
        from app.agents.academic_agent import AcademicPerformanceAgent
        agent = AcademicPerformanceAgent(school_id=school_id, student_id=student_id)
        result = asyncio.run(agent.run())
        logger.info(f"[AcademicAgent] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[AcademicAgent] Failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_attendance_agent_for_student", bind=True, max_retries=3)
def run_attendance_agent_for_student(self, student_id: int, school_id: int):
    """Triggered by attendance.marked event."""
    try:
        logger.info(
            f"[AttendanceAgent] Starting for school_id={school_id} "
            f"student_id={student_id}"
        )
        from app.agents.attendance_agent import AttendanceRiskAgent
        agent = AttendanceRiskAgent(school_id=school_id, student_id=student_id)
        result = asyncio.run(agent.run())
        logger.info(f"[AttendanceAgent] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[AttendanceAgent] Failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_fee_agent_for_student", bind=True, max_retries=3)
def run_fee_agent_for_student(self, student_id: int, school_id: int, fee_id: int = None):
    """Triggered by fee.overdue event."""
    try:
        logger.info(
            f"[FeeAgent] Starting for school_id={school_id} "
            f"student_id={student_id} fee_id={fee_id}"
        )
        from app.agents.fee_agent import FeeCollectionAgent
        agent = FeeCollectionAgent(school_id=school_id, student_id=student_id, fee_id=fee_id)
        result = asyncio.run(agent.run())
        logger.info(f"[FeeAgent] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[FeeAgent] Failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_behavioral_agent_for_student", bind=True, max_retries=3)
def run_behavioral_agent_for_student(self, student_id: int, school_id: int):
    """Triggered by incident.created event."""
    try:
        logger.info(
            f"[BehavioralAgent] Starting for school_id={school_id} "
            f"student_id={student_id}"
        )
        from app.agents.behavioral_agent import BehavioralAgent
        agent = BehavioralAgent(school_id=school_id, student_id=student_id)
        result = asyncio.run(agent.run())
        logger.info(f"[BehavioralAgent] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[BehavioralAgent] Failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_admission_agent_for_lead", bind=True, max_retries=3)
def run_admission_agent_for_lead(self, lead_id: int, school_id: int):
    """Triggered by lead.created event."""
    try:
        logger.info(
            f"[AdmissionAgent] Starting for school_id={school_id} "
            f"lead_id={lead_id}"
        )
        from app.agents.admission_agent import AdmissionAgent
        agent = AdmissionAgent(school_id=school_id, lead_id=lead_id)
        result = asyncio.run(agent.run())
        logger.info(f"[AdmissionAgent] Done: {result}")
        return result
    except Exception as exc:
        logger.error(f"[AdmissionAgent] Failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


# ══════════════════════════════════════════════════════════════════════
# CRON-TRIGGERED TASKS  — safety net if events were missed
# ══════════════════════════════════════════════════════════════════════

@celery_app.task(name="run_academic_agent_all_schools")
def run_academic_agent_all_schools():
    """Cron: 11 PM nightly — catch any missed marks events."""
    from app.core.database import SessionLocal
    from app.models.student import Student
    from app.models.school import School

    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        total   = 0
        for school in schools:
            students = db.query(Student).filter(
                Student.school_id == school.id,
                Student.is_active == True,
            ).all()
            for student in students:
                run_academic_agent_for_student.delay(
                    student_id=student.id,
                    school_id=school.id
                )
                total += 1
        logger.info(f"[Cron] Academic agent dispatched for {total} students")
    except Exception as exc:
        logger.error(f"[Cron] Academic agent failed: {exc}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="run_attendance_agent_all_schools")
def run_attendance_agent_all_schools():
    """Cron: 6 PM nightly — catch any missed attendance events."""
    from app.core.database import SessionLocal
    from app.models.student import Student
    from app.models.school import School

    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        total   = 0
        for school in schools:
            students = db.query(Student).filter(
                Student.school_id == school.id,
                Student.is_active == True,
            ).all()
            for student in students:
                run_attendance_agent_for_student.delay(
                    student_id=student.id,
                    school_id=school.id
                )
                total += 1
        logger.info(f"[Cron] Attendance agent dispatched for {total} students")
    except Exception as exc:
        logger.error(f"[Cron] Attendance agent failed: {exc}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="run_fee_agent_all_schools")
def run_fee_agent_all_schools():
    """Cron: 8 AM daily — scan all schools for overdue fees."""
    from app.core.database import SessionLocal
    from app.models.fee import FeeRecord, FeeStatus
    from app.models.school import School
    from datetime import date

    db = SessionLocal()
    try:
        # Find all fee records that are due or overdue
        fees = db.query(FeeRecord).filter(
            FeeRecord.status.in_([FeeStatus.due, FeeStatus.overdue, FeeStatus.partial]),
            FeeRecord.due_date <= date.today(),
        ).all()

        dispatched = 0
        seen = set()   # avoid dispatching same student twice
        for fee in fees:
            key = (fee.student_id, fee.school_id)
            if key not in seen:
                run_fee_agent_for_student.delay(
                    student_id=fee.student_id,
                    school_id=fee.school_id,
                    fee_id=fee.id
                )
                seen.add(key)
                dispatched += 1

        logger.info(f"[Cron] Fee agent dispatched for {dispatched} students")
    except Exception as exc:
        logger.error(f"[Cron] Fee agent failed: {exc}", exc_info=True)
    finally:
        db.close()


# ── Beat schedule ────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "academic-nightly":   {"task": "run_academic_agent_all_schools",  "schedule": crontab(hour=23, minute=0)},
    "attendance-evening": {"task": "run_attendance_agent_all_schools", "schedule": crontab(hour=18, minute=0)},
    "fee-morning":        {"task": "run_fee_agent_all_schools",        "schedule": crontab(hour=8,  minute=0)},
}
celery_app.conf.update(include=["app.tasks.agent_tasks"])
