# # backend/app/tasks/agent_tasks.py

# from app.tasks import celery_app
# from celery.schedules import crontab
# import logging

# logger = logging.getLogger(__name__)


# # ══════════════════════════════════════════════════════════════════════
# # EVENT-TRIGGERED TASKS
# # These run instantly when a Redis event arrives via subscriber.py
# # ══════════════════════════════════════════════════════════════════════

# @celery_app.task(name="run_academic_agent_for_student", bind=True, max_retries=3)
# def run_academic_agent_for_student(self, student_id: int, school_id: int):
#     """
#     Triggered by: marks.entered event
#     Checks if student's performance has dropped and sends alerts.
#     Full implementation added in Phase 5 when we build the agent.
#     """
#     logger.info(
#         f"[AcademicAgent] Running for student_id={student_id} "
#         f"school_id={school_id}"
#     )
#     # Phase 5: from app.agents.academic_agent import AcademicPerformanceAgent
#     # Phase 5: agent = AcademicPerformanceAgent(school_id, student_id)
#     # Phase 5: asyncio.run(agent.run())
#     logger.info(f"[AcademicAgent] Placeholder — agent will be built in Phase 5")


# @celery_app.task(name="run_attendance_agent_for_student", bind=True, max_retries=3)
# def run_attendance_agent_for_student(self, student_id: int, school_id: int):
#     """Triggered by: attendance.marked event"""
#     logger.info(
#         f"[AttendanceAgent] Running for student_id={student_id} "
#         f"school_id={school_id}"
#     )
#     logger.info("[AttendanceAgent] Placeholder — agent will be built in Phase 5")


# @celery_app.task(name="run_fee_agent_for_student", bind=True, max_retries=3)
# def run_fee_agent_for_student(self, student_id: int, fee_id: int, school_id: int):
#     """Triggered by: fee.overdue event"""
#     logger.info(
#         f"[FeeAgent] Running for student_id={student_id} "
#         f"fee_id={fee_id} school_id={school_id}"
#     )
#     logger.info("[FeeAgent] Placeholder — agent will be built in Phase 5")


# @celery_app.task(name="run_behavioral_agent_for_student", bind=True, max_retries=3)
# def run_behavioral_agent_for_student(self, student_id: int, school_id: int):
#     """Triggered by: incident.created event"""
#     logger.info(
#         f"[BehavioralAgent] Running for student_id={student_id} "
#         f"school_id={school_id}"
#     )
#     logger.info("[BehavioralAgent] Placeholder — agent will be built in Phase 5")


# @celery_app.task(name="run_admission_agent_for_lead", bind=True, max_retries=3)
# def run_admission_agent_for_lead(self, lead_id: int, school_id: int):
#     """Triggered by: lead.created event"""
#     logger.info(
#         f"[AdmissionAgent] Running for lead_id={lead_id} "
#         f"school_id={school_id}"
#     )
#     logger.info("[AdmissionAgent] Placeholder — agent will be built in Phase 5")


# # ══════════════════════════════════════════════════════════════════════
# # CRON-TRIGGERED TASKS  (safety net — run even if events were missed)
# # ══════════════════════════════════════════════════════════════════════

# @celery_app.task(name="run_academic_agent_all_schools")
# def run_academic_agent_all_schools():
#     """
#     Cron: runs every night at 11 PM.
#     Catches any students whose marks events were missed during the day.
#     """
#     logger.info("[CronJob] Running academic agent for all schools...")
#     # Phase 5: loop all active schools → all students → dispatch per-student task
#     logger.info("[CronJob] Academic agent cron placeholder")


# @celery_app.task(name="run_attendance_agent_all_schools")
# def run_attendance_agent_all_schools():
#     """Cron: runs every evening at 6 PM."""
#     logger.info("[CronJob] Running attendance agent for all schools...")
#     logger.info("[CronJob] Attendance agent cron placeholder")


# @celery_app.task(name="run_fee_agent_all_schools")
# def run_fee_agent_all_schools():
#     """Cron: runs every morning at 8 AM. Checks for newly overdue fees."""
#     logger.info("[CronJob] Running fee agent for all schools...")
#     logger.info("[CronJob] Fee agent cron placeholder")


# # ══════════════════════════════════════════════════════════════════════
# # CELERY BEAT SCHEDULE  (cron job definitions)
# # ══════════════════════════════════════════════════════════════════════

# celery_app.conf.beat_schedule = {
#     # Academic Agent: every night 11 PM IST
#     "academic-nightly": {
#         "task":     "run_academic_agent_all_schools",
#         "schedule": crontab(hour=23, minute=0),
#     },
#     # Attendance Agent: every evening 6 PM IST
#     "attendance-evening": {
#         "task":     "run_attendance_agent_all_schools",
#         "schedule": crontab(hour=18, minute=0),
#     },
#     # Fee Agent: every morning 8 AM IST
#     "fee-morning": {
#         "task":     "run_fee_agent_all_schools",
#         "schedule": crontab(hour=8, minute=0),
#     },
# }

# # Update the Celery app's include list to pick up these tasks
# celery_app.conf.update(include=["app.tasks.agent_tasks"])

# # backend/app/tasks/agent_tasks.py  — full replacement

# import asyncio
# import logging

# from app.tasks import celery_app
# from celery.schedules import crontab
# # ADD this import at the top:
# from app.tasks.notification_tasks import flush_notification_queue  # noqa: F401 — imported but not used directly in this file

# logger = logging.getLogger(__name__)


# # ══════════════════════════════════════════════════════════════════════
# # EVENT-TRIGGERED TASKS  — run instantly via subscriber.py
# # ══════════════════════════════════════════════════════════════════════

# @celery_app.task(name="run_academic_agent_for_student", bind=True, max_retries=3)
# def run_academic_agent_for_student(self, student_id: int, school_id: int):
#     """Triggered by marks.entered event."""
#     try:
#         logger.info(
#             f"[AcademicAgent] Starting for school_id={school_id} "
#             f"student_id={student_id}"
#         )
#         from app.agents.academic_agent import AcademicPerformanceAgent
#         agent = AcademicPerformanceAgent(school_id=school_id, student_id=student_id)
#         result = asyncio.run(agent.run())
#         logger.info(f"[AcademicAgent] Done: {result}")
#         return result
#     except Exception as exc:
#         logger.error(f"[AcademicAgent] Failed: {exc}")
#         raise self.retry(exc=exc, countdown=60)   # retry in 60 seconds


# @celery_app.task(name="run_attendance_agent_for_student", bind=True, max_retries=3)
# def run_attendance_agent_for_student(self, student_id: int, school_id: int):
#     """Triggered by attendance.marked event."""
#     try:
#         from app.agents.attendance_agent import AttendanceRiskAgent
#         agent = AttendanceRiskAgent(school_id=school_id, student_id=student_id)
#         result = asyncio.run(agent.run())
#         logger.info(f"[AttendanceAgent] Done: {result}")
#         return result
#     except Exception as exc:
#         logger.error(f"[AttendanceAgent] Failed: {exc}")
#         raise self.retry(exc=exc, countdown=60)


# @celery_app.task(name="run_fee_agent_for_student", bind=True, max_retries=3)
# def run_fee_agent_for_student(self, student_id: int, school_id: int, fee_id: int = None):
#     """Triggered by fee.overdue event."""
#     try:
#         from app.agents.fee_agent import FeeCollectionAgent
#         agent = FeeCollectionAgent(school_id=school_id, student_id=student_id, fee_id=fee_id)
#         result = asyncio.run(agent.run())
#         logger.info(f"[FeeAgent] Done: {result}")
#         return result
#     except Exception as exc:
#         logger.error(f"[FeeAgent] Failed: {exc}")
#         raise self.retry(exc=exc, countdown=60)


# @celery_app.task(name="run_behavioral_agent_for_student", bind=True, max_retries=3)
# def run_behavioral_agent_for_student(self, student_id: int, school_id: int):
#     """Triggered by incident.created event. Full agent built in Phase 9."""
#     logger.info(f"[BehavioralAgent] Queued for student_id={student_id} — Phase 9")


# @celery_app.task(name="run_admission_agent_for_lead", bind=True, max_retries=3)
# def run_admission_agent_for_lead(self, lead_id: int, school_id: int):
#     """Triggered by lead.created event. Full agent built in Phase 9."""
#     logger.info(f"[AdmissionAgent] Queued for lead_id={lead_id} — Phase 9")


# # ══════════════════════════════════════════════════════════════════════
# # CRON-TRIGGERED TASKS  — safety net if events were missed
# # ══════════════════════════════════════════════════════════════════════

# @celery_app.task(name="run_academic_agent_all_schools")
# def run_academic_agent_all_schools():
#     """Cron: 11 PM nightly — catch any missed marks events."""
#     from app.core.database import SessionLocal
#     from app.models.student import Student
#     from app.models.school import School

#     db = SessionLocal()
#     try:
#         schools = db.query(School).filter(School.is_active == True).all()
#         total   = 0
#         for school in schools:
#             students = db.query(Student).filter(
#                 Student.school_id == school.id,
#                 Student.is_active == True,
#             ).all()
#             for student in students:
#                 run_academic_agent_for_student.delay(
#                     student_id=student.id,
#                     school_id=school.id
#                 )
#                 total += 1
#         logger.info(f"[Cron] Academic agent dispatched for {total} students")
#     finally:
#         db.close()


# @celery_app.task(name="run_attendance_agent_all_schools")
# def run_attendance_agent_all_schools():
#     """Cron: 6 PM nightly — catch any missed attendance events."""
#     from app.core.database import SessionLocal
#     from app.models.student import Student
#     from app.models.school import School

#     db = SessionLocal()
#     try:
#         schools = db.query(School).filter(School.is_active == True).all()
#         total   = 0
#         for school in schools:
#             students = db.query(Student).filter(
#                 Student.school_id == school.id,
#                 Student.is_active == True,
#             ).all()
#             for student in students:
#                 run_attendance_agent_for_student.delay(
#                     student_id=student.id,
#                     school_id=school.id
#                 )
#                 total += 1
#         logger.info(f"[Cron] Attendance agent dispatched for {total} students")
#     finally:
#         db.close()


# @celery_app.task(name="run_fee_agent_all_schools")
# def run_fee_agent_all_schools():
#     """Cron: 8 AM daily — scan all schools for overdue fees."""
#     from app.core.database import SessionLocal
#     from app.models.fee import FeeRecord, FeeStatus
#     from app.models.school import School
#     from datetime import date

#     db = SessionLocal()
#     try:
#         # Find all fee records that are due or overdue
#         fees = db.query(FeeRecord).filter(
#             FeeRecord.status.in_([FeeStatus.due, FeeStatus.overdue, FeeStatus.partial]),
#             FeeRecord.due_date <= date.today(),
#         ).all()

#         dispatched = 0
#         seen = set()   # avoid dispatching same student twice
#         for fee in fees:
#             key = (fee.student_id, fee.school_id)
#             if key not in seen:
#                 run_fee_agent_for_student.delay(
#                     student_id=fee.student_id,
#                     school_id=fee.school_id,
#                     fee_id=fee.id
#                 )
#                 seen.add(key)
#                 dispatched += 1

#         logger.info(f"[Cron] Fee agent dispatched for {dispatched} students")
#     finally:
#         db.close()


# # # ── Beat schedule ────────────────────────────────────────────────────
# # celery_app.conf.beat_schedule = {
# #     "academic-nightly":   {"task": "run_academic_agent_all_schools",  "schedule": crontab(hour=23, minute=0)},
# #     "attendance-evening": {"task": "run_attendance_agent_all_schools", "schedule": crontab(hour=18, minute=0)},
# #     "fee-morning":        {"task": "run_fee_agent_all_schools",        "schedule": crontab(hour=8,  minute=0)},
# # }
# # celery_app.conf.update(include=["app.tasks.agent_tasks"])

# # backend/app/tasks/agent_tasks.py


# # UPDATE celery_app.conf.beat_schedule — add the flush entry:
# celery_app.conf.beat_schedule = {
#     # ── Agent cron jobs ──────────────────────────────────────────
#     "academic-nightly": {
#         "task":     "run_academic_agent_all_schools",
#         "schedule": crontab(hour=23, minute=0),
#     },
#     "attendance-evening": {
#         "task":     "run_attendance_agent_all_schools",
#         "schedule": crontab(hour=18, minute=0),
#     },
#     "fee-morning": {
#         "task":     "run_fee_agent_all_schools",
#         "schedule": crontab(hour=8, minute=0),
#     },
#     # ── Notification queue flusher ───────────────────────────────
#     # Runs every 2 minutes — picks up pending notifications and sends them
#     "flush-notifications": {
#         "task":     "flush_notification_queue",
#         "schedule": crontab(minute="*/2"),   # every 2 minutes
#     },
# }

# # UPDATE include list:
# celery_app.conf.update(
#     include=[
#         "app.tasks.agent_tasks",
#         "app.tasks.notification_tasks",   # ← add this
#     ]
# )

# backend/app/tasks/agent_tasks.py  — complete final version

import asyncio
import logging

from app.tasks import celery_app
from celery.schedules import crontab

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# EVENT-TRIGGERED TASKS
# ══════════════════════════════════════════════════════════

@celery_app.task(name="run_academic_agent_for_student", bind=True, max_retries=3)
def run_academic_agent_for_student(self, student_id: int, school_id: int):
    try:
        from app.agents.academic_agent import AcademicPerformanceAgent
        result = asyncio.run(
            AcademicPerformanceAgent(school_id, student_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_attendance_agent_for_student", bind=True, max_retries=3)
def run_attendance_agent_for_student(self, student_id: int, school_id: int):
    try:
        from app.agents.attendance_agent import AttendanceRiskAgent
        result = asyncio.run(
            AttendanceRiskAgent(school_id, student_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_fee_agent_for_student", bind=True, max_retries=3)
def run_fee_agent_for_student(self, student_id: int, school_id: int,
                               fee_id: int = None):
    try:
        from app.agents.fee_agent import FeeCollectionAgent
        result = asyncio.run(
            FeeCollectionAgent(school_id, student_id, fee_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_behavioral_agent_for_student", bind=True, max_retries=3)
def run_behavioral_agent_for_student(self, student_id: int, school_id: int):
    try:
        from app.agents.behavioral_agent import BehavioralMonitorAgent
        result = asyncio.run(
            BehavioralMonitorAgent(school_id, student_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_admission_agent_for_lead", bind=True, max_retries=3)
def run_admission_agent_for_lead(self, lead_id: int, school_id: int):
    try:
        from app.agents.admission_agent import AdmissionLeadAgent
        result = asyncio.run(
            AdmissionLeadAgent(school_id, lead_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ══════════════════════════════════════════════════════════
# CRON-TRIGGERED TASKS
# ══════════════════════════════════════════════════════════

def _get_active_schools_and_students(db):
    from app.models.school import School
    from app.models.student import Student
    schools  = db.query(School).filter(School.is_active == True).all()
    students_map = {}
    for school in schools:
        students_map[school.id] = db.query(Student).filter(
            Student.school_id == school.id,
            Student.is_active == True,
        ).all()
    return schools, students_map


@celery_app.task(name="run_academic_agent_all_schools")
def run_academic_agent_all_schools():
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        schools, students_map = _get_active_schools_and_students(db)
        total = 0
        for school in schools:
            for s in students_map.get(school.id, []):
                run_academic_agent_for_student.delay(s.id, school.id)
                total += 1
        logger.info(f"[Cron] Academic → {total} students")
    finally:
        db.close()


@celery_app.task(name="run_attendance_agent_all_schools")
def run_attendance_agent_all_schools():
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        schools, students_map = _get_active_schools_and_students(db)
        total = 0
        for school in schools:
            for s in students_map.get(school.id, []):
                run_attendance_agent_for_student.delay(s.id, school.id)
                total += 1
        logger.info(f"[Cron] Attendance → {total} students")
    finally:
        db.close()


@celery_app.task(name="run_fee_agent_all_schools")
def run_fee_agent_all_schools():
    from app.core.database import SessionLocal
    from app.models.fee import FeeRecord, FeeStatus
    from datetime import date
    db = SessionLocal()
    try:
        fees = db.query(FeeRecord).filter(
            FeeRecord.status.in_([FeeStatus.due, FeeStatus.overdue,
                                   FeeStatus.partial]),
            FeeRecord.due_date <= date.today(),
        ).all()
        seen = set()
        dispatched = 0
        for fee in fees:
            key = (fee.student_id, fee.school_id)
            if key not in seen:
                run_fee_agent_for_student.delay(
                    fee.student_id, fee.school_id, fee.id
                )
                seen.add(key)
                dispatched += 1
        logger.info(f"[Cron] Fee → {dispatched} students")
    finally:
        db.close()


@celery_app.task(name="run_teacher_copilot_all_schools")
def run_teacher_copilot_all_schools():
    """Cron: 1st of every month — proactive suggestions to teachers."""
    from app.core.database import SessionLocal
    from app.models.school import School
    from app.models.class_ import Class_
    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        for school in schools:
            classes = db.query(Class_).filter(
                Class_.school_id == school.id,
            ).all()
            for cls in classes:
                if cls.class_teacher_id:
                    run_teacher_copilot_for_class.delay(
                        school.id, cls.id, cls.class_teacher_id
                    )
    finally:
        db.close()


@celery_app.task(name="run_teacher_copilot_for_class", bind=True, max_retries=2)
def run_teacher_copilot_for_class(self, school_id: int, class_id: int,
                                   teacher_id: int):
    try:
        from app.agents.teacher_copilot_agent import TeacherCopilotAgent
        result = asyncio.run(
            TeacherCopilotAgent(school_id, class_id, teacher_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="run_teacher_performance_all_schools")
def run_teacher_performance_all_schools():
    """Cron: 1st of every month."""
    from app.core.database import SessionLocal
    from app.models.school import School
    from app.models.user import User, UserRole
    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        for school in schools:
            teachers = db.query(User).filter(
                User.school_id == school.id,
                User.role      == UserRole.teacher,
                User.is_active == True,
            ).all()
            for teacher in teachers:
                run_teacher_performance_for_teacher.delay(
                    school.id, teacher.id
                )
    finally:
        db.close()


@celery_app.task(name="run_teacher_performance_for_teacher",
                 bind=True, max_retries=2)
def run_teacher_performance_for_teacher(self, school_id: int, teacher_id: int):
    try:
        from app.agents.teacher_performance_agent import TeacherPerformanceAgent
        result = asyncio.run(
            TeacherPerformanceAgent(school_id, teacher_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="run_behavioral_agent_all_schools")
def run_behavioral_agent_all_schools():
    """Cron: Every Sunday night."""
    from app.core.database import SessionLocal
    from app.models.school import School
    from app.models.student import Student
    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        total = 0
        for school in schools:
            students = db.query(Student).filter(
                Student.school_id == school.id,
                Student.is_active == True,
            ).all()
            for s in students:
                run_behavioral_agent_for_student.delay(s.id, school.id)
                total += 1
        logger.info(f"[Cron] Behavioral → {total} students")
    finally:
        db.close()


@celery_app.task(name="run_admin_workflow_all_schools")
def run_admin_workflow_all_schools():
    """Cron: Daily 7 AM."""
    from app.core.database import SessionLocal
    from app.models.school import School
    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        for school in schools:
            run_admin_workflow_for_school.delay(school.id)
    finally:
        db.close()


@celery_app.task(name="run_admin_workflow_for_school", bind=True, max_retries=2)
def run_admin_workflow_for_school(self, school_id: int):
    try:
        from app.agents.admin_workflow_agent import AdminWorkflowAgent
        result = asyncio.run(AdminWorkflowAgent(school_id).run())
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="run_learning_agent_all_schools")
def run_learning_agent_all_schools():
    """Cron: Every Sunday 8 PM."""
    from app.core.database import SessionLocal
    from app.models.school import School
    from app.models.student import Student
    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        total = 0
        for school in schools:
            students = db.query(Student).filter(
                Student.school_id == school.id,
                Student.is_active == True,
            ).all()
            for s in students:
                run_learning_agent_for_student.delay(s.id, school.id)
                total += 1
        logger.info(f"[Cron] Learning → {total} students")
    finally:
        db.close()


@celery_app.task(name="run_learning_agent_for_student", bind=True, max_retries=2)
def run_learning_agent_for_student(self, student_id: int, school_id: int):
    try:
        from app.agents.learning_agent import PersonalizedLearningAgent
        result = asyncio.run(
            PersonalizedLearningAgent(school_id, student_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="run_parent_comm_agent_all_schools")
def run_parent_comm_agent_all_schools():
    """Cron: Every 15 minutes — processes pending translation queue."""
    from app.core.database import SessionLocal
    from app.models.school import School
    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        for school in schools:
            run_parent_comm_for_school.delay(school.id)
    finally:
        db.close()


@celery_app.task(name="run_parent_comm_for_school", bind=True, max_retries=2)
def run_parent_comm_for_school(self, school_id: int):
    try:
        from app.agents.parent_comm_agent import ParentCommunicationAgent
        result = asyncio.run(
            ParentCommunicationAgent(school_id).run()
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="run_admission_followup_all_schools")
def run_admission_followup_all_schools():
    """Cron: Every hour — check pending lead follow-ups."""
    from app.core.database import SessionLocal
    from app.models.school import School
    from app.models.lead import Lead, LeadStatus
    db = SessionLocal()
    try:
        schools = db.query(School).filter(School.is_active == True).all()
        total = 0
        for school in schools:
            leads = db.query(Lead).filter(
                Lead.school_id == school.id,
                Lead.status.notin_([
                    LeadStatus.admitted,
                    LeadStatus.rejected,
                    LeadStatus.lost,
                ]),
            ).all()
            for lead in leads:
                run_admission_agent_for_lead.delay(lead.id, school.id)
                total += 1
        logger.info(f"[Cron] Admission → {total} leads checked")
    finally:
        db.close()


# ══════════════════════════════════════════════════════════
# BEAT SCHEDULE — all 10 agents
# ══════════════════════════════════════════════════════════

celery_app.conf.beat_schedule = {
    # Agents 1–3 (from Phase 5)
    "academic-nightly": {
        "task":     "run_academic_agent_all_schools",
        "schedule": crontab(hour=23, minute=0),
    },
    "attendance-evening": {
        "task":     "run_attendance_agent_all_schools",
        "schedule": crontab(hour=18, minute=0),
    },
    "fee-morning": {
        "task":     "run_fee_agent_all_schools",
        "schedule": crontab(hour=8, minute=0),
    },
    # Agent 4 — Teacher Co-Pilot
    "teacher-copilot-monthly": {
        "task":     "run_teacher_copilot_all_schools",
        "schedule": crontab(hour=9, minute=0, day_of_month="1"),
    },
    # Agent 5 — Admission Lead
    "admission-followup-hourly": {
        "task":     "run_admission_followup_all_schools",
        "schedule": crontab(minute=0),   # top of every hour
    },
    # Agent 6 — Teacher Performance
    "teacher-performance-monthly": {
        "task":     "run_teacher_performance_all_schools",
        "schedule": crontab(hour=10, minute=0, day_of_month="1"),
    },
    # Agent 7 — Behavioral Monitor
    "behavioral-weekly": {
        "task":     "run_behavioral_agent_all_schools",
        "schedule": crontab(hour=20, minute=0, day_of_week="0"),  # Sunday 8 PM
    },
    # Agent 8 — Admin Workflow
    "admin-workflow-daily": {
        "task":     "run_admin_workflow_all_schools",
        "schedule": crontab(hour=7, minute=0),
    },
    # Agent 9 — Personalized Learning
    "learning-weekly": {
        "task":     "run_learning_agent_all_schools",
        "schedule": crontab(hour=20, minute=0, day_of_week="0"),  # Sunday 8 PM
    },
    # Agent 10 — Parent Communication (translation)
    "parent-comm-15min": {
        "task":     "run_parent_comm_agent_all_schools",
        "schedule": crontab(minute="*/15"),   # every 15 minutes
    },
}

celery_app.conf.update(include=["app.tasks.agent_tasks"])