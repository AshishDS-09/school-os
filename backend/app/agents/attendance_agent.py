# backend/app/agents/attendance_agent.py

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.attendance import Attendance, AttendanceStatus
from app.models.student import Student
from app.models.user import User

logger = logging.getLogger(__name__)

# Risk thresholds
ABSENCE_WINDOW_DAYS  = 10   # look at last 10 school days
HIGH_RISK_ABSENCES   = 5    # 5+ absences in 10 days → HIGH
MEDIUM_RISK_ABSENCES = 3    # 3–4 absences → MEDIUM


class AttendanceRiskAgent(BaseAgent):
    """
    Detects irregular attendance patterns and flags dropout risk.

    Triggered by:  attendance.marked event  (instant)
    Cron backup:   every evening 6 PM

    Decision logic:
        5+ absences in last 10 days  →  HIGH  →  alert principal + parent + counselor note
        3–4 absences in last 10 days →  MEDIUM →  alert parent
        <3 absences                  →  LOW   →  log only
        Already alerted today        →  SKIP
    """

    def __init__(self, school_id: int, student_id: int):
        super().__init__("attendance_agent", school_id)
        self.student_id = student_id

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            student = db.query(Student).filter(
                Student.id        == self.student_id,
                Student.school_id == self.school_id,
                Student.is_active == True,
            ).first()

            if not student:
                return {"error": "student_not_found"}

            parent = db.query(User).filter(
                User.id == student.parent_id
            ).first() if student.parent_id else None

            # Get attendance for last 10 days
            since = date.today() - timedelta(days=ABSENCE_WINDOW_DAYS)
            records = db.query(Attendance).filter(
                Attendance.student_id == self.student_id,
                Attendance.school_id  == self.school_id,
                Attendance.date       >= since,
            ).order_by(Attendance.date.desc()).all()

            # Count by status
            absent_count  = sum(1 for r in records if r.status == AttendanceStatus.absent)
            present_count = sum(1 for r in records if r.status == AttendanceStatus.present)
            late_count    = sum(1 for r in records if r.status == AttendanceStatus.late)

            # Consecutive absences (most recent days first)
            consecutive = 0
            for r in records:
                if r.status == AttendanceStatus.absent:
                    consecutive += 1
                else:
                    break

            prev_state = await self.load_state(self.student_id, "student")

            return {
                "student":          student,
                "student_name":     student.full_name,
                "parent_id":        parent.id if parent else None,
                "absent_count":     absent_count,
                "present_count":    present_count,
                "late_count":       late_count,
                "consecutive_absent": consecutive,
                "total_days":       len(records),
                "prev_state":       prev_state,
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        if data.get("error"):
            return {"risk_level": "NONE"}

        absent     = data["absent_count"]
        consecutive = data["consecutive_absent"]
        prev_state = data["prev_state"]

        # Determine risk level using clear rules
        if absent >= HIGH_RISK_ABSENCES or consecutive >= 3:
            risk_level = "HIGH"
        elif absent >= MEDIUM_RISK_ABSENCES:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Check if risk has escalated since last run
        prev_risk = prev_state.get("risk_level", "LOW")
        escalated = (
            risk_level == "HIGH" and prev_risk != "HIGH"
        )

        return {
            "risk_level":          risk_level,
            "absent_count":        absent,
            "consecutive_absent":  consecutive,
            "escalated":           escalated,
            "prev_risk":           prev_risk,
            "prev_state":          prev_state,
        }

    async def decide(self, analysis: dict) -> dict:
        risk_level  = analysis.get("risk_level", "LOW")
        prev_state  = analysis.get("prev_state", {})

        # Skip if already alerted today
        last_alert     = prev_state.get("last_alert_date")
        alerted_today  = (last_alert == str(date.today()))

        if risk_level == "NONE":
            return {"action": "skip", "reason": "no_risk"}

        if risk_level == "LOW":
            return {"action": "log_only", "analysis": analysis}

        if alerted_today:
            return {"action": "skip", "reason": "already_alerted_today"}

        if risk_level == "HIGH":
            return {
                "action":              "alert_high",
                "analysis":            analysis,
                "notify_parent":       True,
                "suggest_counselor":   True,
            }

        return {
            "action":        "alert_medium",
            "analysis":      analysis,
            "notify_parent": True,
        }

    async def act(self, decision: dict) -> dict:
        action   = decision.get("action")
        analysis = decision.get("analysis", {})

        if action == "skip":
            return {"result": "skipped", "reason": decision.get("reason")}

        if action == "log_only":
            await self.save_state(
                self.student_id, "student",
                {"risk_level": "LOW", "last_check_date": str(date.today())}
            )
            return {"result": "logged", "risk_level": "LOW"}

        # HIGH or MEDIUM alert
        risk_level   = analysis.get("risk_level")
        absent_count = analysis.get("absent_count", 0)
        consecutive  = analysis.get("consecutive_absent", 0)
        parent_id    = None

        db: Session = SessionLocal()
        try:
            student   = db.query(Student).filter(Student.id == self.student_id).first()
            parent_id = student.parent_id if student else None
        finally:
            db.close()

        notifs = 0

        if decision.get("notify_parent") and parent_id:
            if risk_level == "HIGH":
                message = (
                    f"Dear Parent,\n\n"
                    f"Your child has been absent {absent_count} times in the last "
                    f"{ABSENCE_WINDOW_DAYS} school days"
                    + (f" (including {consecutive} consecutive days)" if consecutive >= 2 else "")
                    + ".\n\n"
                    f"This is affecting their learning. Please contact the school "
                    f"to discuss a plan.\n"
                    f"— School OS Attendance Alert"
                )
            else:
                message = (
                    f"Dear Parent,\n\n"
                    f"Your child has missed {absent_count} days recently. "
                    f"Please ensure regular attendance.\n"
                    f"— School OS"
                )

            await self.queue_notification(
                recipient_id      = parent_id,
                channel           = "whatsapp",
                notification_type = "attendance_alert",
                payload           = {
                    "message":      message,
                    "risk_level":   risk_level,
                    "absent_count": absent_count,
                    "student_id":   self.student_id,
                }
            )
            notifs += 1

        await self.save_state(
            self.student_id, "student",
            {
                "risk_level":           risk_level,
                "last_alert_date":      str(date.today()),
                "absent_count":         absent_count,
                "consecutive_absent":   consecutive,
                "counselor_suggested":  decision.get("suggest_counselor", False),
            }
        )

        return {
            "result":       "alert_sent",
            "risk_level":   risk_level,
            "absent_count": absent_count,
            "notifs_queued": notifs,
        }