# backend/app/tasks/agent_tasks.py

from app.tasks import celery_app
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# EVENT-TRIGGERED TASKS
# These run instantly when a Redis event arrives via subscriber.py
# ══════════════════════════════════════════════════════════════════════

@celery_app.task(name="run_academic_agent_for_student", bind=True, max_retries=3)
def run_academic_agent_for_student(self, student_id: int, school_id: int):
    """
    Triggered by: marks.entered event
    Checks if student's performance has dropped and sends alerts.
    Full implementation added in Phase 5 when we build the agent.
    """
    logger.info(
        f"[AcademicAgent] Running for student_id={student_id} "
        f"school_id={school_id}"
    )
    # Phase 5: from app.agents.academic_agent import AcademicPerformanceAgent
    # Phase 5: agent = AcademicPerformanceAgent(school_id, student_id)
    # Phase 5: asyncio.run(agent.run())
    logger.info(f"[AcademicAgent] Placeholder — agent will be built in Phase 5")


@celery_app.task(name="run_attendance_agent_for_student", bind=True, max_retries=3)
def run_attendance_agent_for_student(self, student_id: int, school_id: int):
    """Triggered by: attendance.marked event"""
    logger.info(
        f"[AttendanceAgent] Running for student_id={student_id} "
        f"school_id={school_id}"
    )
    logger.info("[AttendanceAgent] Placeholder — agent will be built in Phase 5")


@celery_app.task(name="run_fee_agent_for_student", bind=True, max_retries=3)
def run_fee_agent_for_student(self, student_id: int, fee_id: int, school_id: int):
    """Triggered by: fee.overdue event"""
    logger.info(
        f"[FeeAgent] Running for student_id={student_id} "
        f"fee_id={fee_id} school_id={school_id}"
    )
    logger.info("[FeeAgent] Placeholder — agent will be built in Phase 5")


@celery_app.task(name="run_behavioral_agent_for_student", bind=True, max_retries=3)
def run_behavioral_agent_for_student(self, student_id: int, school_id: int):
    """Triggered by: incident.created event"""
    logger.info(
        f"[BehavioralAgent] Running for student_id={student_id} "
        f"school_id={school_id}"
    )
    logger.info("[BehavioralAgent] Placeholder — agent will be built in Phase 5")


@celery_app.task(name="run_admission_agent_for_lead", bind=True, max_retries=3)
def run_admission_agent_for_lead(self, lead_id: int, school_id: int):
    """Triggered by: lead.created event"""
    logger.info(
        f"[AdmissionAgent] Running for lead_id={lead_id} "
        f"school_id={school_id}"
    )
    logger.info("[AdmissionAgent] Placeholder — agent will be built in Phase 5")


# ══════════════════════════════════════════════════════════════════════
# CRON-TRIGGERED TASKS  (safety net — run even if events were missed)
# ══════════════════════════════════════════════════════════════════════

@celery_app.task(name="run_academic_agent_all_schools")
def run_academic_agent_all_schools():
    """
    Cron: runs every night at 11 PM.
    Catches any students whose marks events were missed during the day.
    """
    logger.info("[CronJob] Running academic agent for all schools...")
    # Phase 5: loop all active schools → all students → dispatch per-student task
    logger.info("[CronJob] Academic agent cron placeholder")


@celery_app.task(name="run_attendance_agent_all_schools")
def run_attendance_agent_all_schools():
    """Cron: runs every evening at 6 PM."""
    logger.info("[CronJob] Running attendance agent for all schools...")
    logger.info("[CronJob] Attendance agent cron placeholder")


@celery_app.task(name="run_fee_agent_all_schools")
def run_fee_agent_all_schools():
    """Cron: runs every morning at 8 AM. Checks for newly overdue fees."""
    logger.info("[CronJob] Running fee agent for all schools...")
    logger.info("[CronJob] Fee agent cron placeholder")


# ══════════════════════════════════════════════════════════════════════
# CELERY BEAT SCHEDULE  (cron job definitions)
# ══════════════════════════════════════════════════════════════════════

celery_app.conf.beat_schedule = {
    # Academic Agent: every night 11 PM IST
    "academic-nightly": {
        "task":     "run_academic_agent_all_schools",
        "schedule": crontab(hour=23, minute=0),
    },
    # Attendance Agent: every evening 6 PM IST
    "attendance-evening": {
        "task":     "run_attendance_agent_all_schools",
        "schedule": crontab(hour=18, minute=0),
    },
    # Fee Agent: every morning 8 AM IST
    "fee-morning": {
        "task":     "run_fee_agent_all_schools",
        "schedule": crontab(hour=8, minute=0),
    },
}

# Update the Celery app's include list to pick up these tasks
celery_app.conf.update(include=["app.tasks.agent_tasks"])