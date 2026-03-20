# backend/app/agents/academic_agent.py

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.models.marks import Marks
from app.models.student import Student
from app.models.user import User

logger = logging.getLogger(__name__)

# Risk thresholds
DROP_THRESHOLD_HIGH   = 15.0   # % drop → HIGH risk
DROP_THRESHOLD_MEDIUM = 8.0    # % drop → MEDIUM risk
MIN_MARKS_FOR_ANALYSIS = 2     # need at least 2 marks to detect a trend
LOOKBACK_DAYS = 45             # compare marks from last 45 days

DEFAULT_REMEDIAL_TOPICS = {
    "mathematics": ["Fractions", "Word Problems", "Algebra Basics"],
    "science": ["Diagrams", "Definitions", "Concept Revision"],
    "english": ["Grammar", "Reading Comprehension", "Vocabulary"],
    "social science": ["Map Practice", "Key Dates", "Short Answers"],
}


class AcademicPerformanceAgent(BaseAgent):
    """
    Detects academic performance decline and sends alerts.

    Triggered by:  marks.entered event  (instant)
    Cron backup:   every night 11 PM    (safety net)

    Decision logic:
        Score dropped >15% vs previous average  →  HIGH  →  alert + remedial plan
        Score dropped  8–15%                    →  MEDIUM →  gentle reminder
        Score dropped <8% or improved           →  LOW   →  log only, no alert
        Agent already alerted today             →  SKIP  →  prevent spam
    """

    def __init__(self, school_id: int, student_id: int):
        super().__init__("academic_agent", school_id)
        self.student_id = student_id

    # ── Step 1: Fetch data ────────────────────────────────────────────

    async def fetch_data(self) -> dict:
        """
        Load:  recent marks (last 45 days)
               student profile + parent info
               previous agent state (to avoid duplicate alerts)
        """
        db: Session = SessionLocal()
        try:
            # Load student with parent relationship
            student = db.query(Student).filter(
                Student.id        == self.student_id,
                Student.school_id == self.school_id,
                Student.is_active == True,
            ).first()

            if not student:
                return {"error": "student_not_found"}

            # Load parent user (for notification)
            parent = db.query(User).filter(
                User.id == student.parent_id
            ).first() if student.parent_id else None

            # Load marks from last 45 days, ordered by date
            since = date.today() - timedelta(days=LOOKBACK_DAYS)
            marks = db.query(Marks).filter(
                Marks.student_id == self.student_id,
                Marks.school_id  == self.school_id,
                Marks.exam_date  >= since,
            ).order_by(Marks.exam_date.asc()).all()

            # Group marks by subject for per-subject trend analysis
            marks_by_subject: dict[str, list[float]] = {}
            for m in marks:
                marks_by_subject.setdefault(m.subject, []).append(m.percentage)

            # Load previous state
            prev_state = await self.load_state(self.student_id, "student")

            return {
                "student":           student,
                "student_name":      student.full_name,
                "parent_id":         parent.id if parent else None,
                "parent_phone":      parent.phone if parent else None,
                "parent_language":   parent.language if parent else "en",
                "marks_by_subject":  marks_by_subject,
                "total_marks_count": len(marks),
                "prev_state":        prev_state,
            }
        finally:
            db.close()

    # ── Step 2: Analyze ───────────────────────────────────────────────

    async def analyze(self, data: dict) -> dict:
        """
        Detect performance trends per subject using local rules.
        Returns risk level and weak subjects.
        """
        if data.get("error"):
            return {
                "risk_level": "NONE",
                "reason": data["error"],
                "prev_state": data.get("prev_state", {}),
            }

        marks_by_subject = data["marks_by_subject"]

        # Need at least some marks to analyze
        if not marks_by_subject or data["total_marks_count"] < MIN_MARKS_FOR_ANALYSIS:
            return {
                "risk_level":    "NONE",
                "reason":        "insufficient_data",
                "weak_subjects": [],
                "prev_state":    data.get("prev_state", {}),
            }

        subject_summary = {}
        for subject, percentages in marks_by_subject.items():
            if len(percentages) >= 2:
                drop = round(percentages[0] - percentages[-1], 1)
                subject_summary[subject] = {
                    "scores":  percentages,
                    "latest":  percentages[-1],
                    "average": round(sum(percentages) / len(percentages), 1),
                    "drop":    drop,
                }

        if not subject_summary:
            return {
                "risk_level":    "NONE",
                "reason":        "only_one_mark_per_subject",
                "weak_subjects": [],
                "prev_state":    data.get("prev_state", {}),
            }

        biggest_drop_subject = max(
            subject_summary,
            key=lambda subject: subject_summary[subject]["drop"]
        )
        biggest_drop_percent = subject_summary[biggest_drop_subject]["drop"]

        weak_subjects = [
            subject for subject, stats in subject_summary.items()
            if stats["drop"] >= DROP_THRESHOLD_MEDIUM
        ]

        if biggest_drop_percent > DROP_THRESHOLD_HIGH:
            risk_level = "HIGH"
        elif biggest_drop_percent >= DROP_THRESHOLD_MEDIUM:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if risk_level == "LOW":
            summary = "Recent marks are stable with no meaningful decline detected."
        else:
            summary = (
                f"{data['student_name']} shows a {biggest_drop_percent:.0f}% drop "
                f"in {biggest_drop_subject}."
            )

        remedial_topics = DEFAULT_REMEDIAL_TOPICS.get(
            biggest_drop_subject.lower(),
            ["Core Concepts", "Practice Questions", "Revision Exercises"],
        )

        return {
            "risk_level": risk_level,
            "weak_subjects": weak_subjects,
            "biggest_drop_subject": biggest_drop_subject,
            "biggest_drop_percent": biggest_drop_percent,
            "summary": summary,
            "remedial_topics": remedial_topics,
            "prev_state": data.get("prev_state", {}),
        }

    # ── Step 3: Decide ────────────────────────────────────────────────

    async def decide(self, analysis: dict) -> dict:
        """
        Decide what action to take based on risk level and previous state.
        Key logic: prevent duplicate alerts — don't alert twice on the same day.
        """
        risk_level  = analysis.get("risk_level", "NONE")
        prev_state  = analysis.get("prev_state", {})

        # Check: did we already alert today?
        last_alert  = prev_state.get("last_alert_date")
        alerted_today = (last_alert == str(date.today()))

        if risk_level == "NONE":
            return {"action": "skip", "reason": "no_risk_detected"}

        if alerted_today:
            return {"action": "skip", "reason": "already_alerted_today"}

        if risk_level == "HIGH":
            return {
                "action":      "alert_high",
                "analysis":    analysis,
                "send_to_parent":  True,
                "send_to_teacher": True,
            }

        if risk_level == "MEDIUM":
            # Only alert parent on MEDIUM — don't escalate to teacher
            return {
                "action":      "alert_medium",
                "analysis":    analysis,
                "send_to_parent":  True,
                "send_to_teacher": False,
            }

        # LOW risk — just update state silently
        return {
            "action":   "log_only",
            "analysis": analysis,
        }

    # ── Step 4: Act ───────────────────────────────────────────────────

    async def act(self, decision: dict) -> dict:
        """
        Execute the decision: queue notifications, update agent state.
        """
        action   = decision.get("action")
        analysis = decision.get("analysis", {})

        # ── Skip: nothing to do ──────────────────────────────────────
        if action == "skip":
            logger.info(
                f"[AcademicAgent] Skipping student_id={self.student_id}: "
                f"{decision.get('reason')}"
            )
            return {"result": "skipped", "reason": decision.get("reason")}

        # ── Log only (LOW risk) ──────────────────────────────────────
        if action == "log_only":
            await self.save_state(
                entity_id   = self.student_id,
                entity_type = "student",
                state       = {
                    "risk_level":      analysis.get("risk_level"),
                    "last_check_date": str(date.today()),
                    "weak_subjects":   analysis.get("weak_subjects", []),
                }
            )
            return {"result": "logged", "risk_level": "LOW"}

        # ── HIGH or MEDIUM alert ─────────────────────────────────────
        risk_level     = analysis.get("risk_level")
        weak_subjects  = analysis.get("weak_subjects", [])
        summary        = analysis.get("summary", "")
        biggest_drop   = analysis.get("biggest_drop_subject", "")
        drop_pct       = analysis.get("biggest_drop_percent", 0)
        remedial_topics = analysis.get("remedial_topics", [])

        # Fetch fresh data needed for notification text
        db: Session = SessionLocal()
        try:
            student = db.query(Student).filter(
                Student.id == self.student_id
            ).first()
            parent_id = student.parent_id if student else None
        finally:
            db.close()

        notifications_queued = 0

        # ── Queue parent notification ────────────────────────────────
        if decision.get("send_to_parent") and parent_id:
            if risk_level == "HIGH":
                message = (
                    f"Dear Parent,\n\n"
                    f"We have noticed that your child's performance has dropped "
                    f"significantly in {biggest_drop} (down {drop_pct:.0f}%).\n\n"
                    f"Weak subjects: {', '.join(weak_subjects)}\n"
                    f"Suggested revision topics: {', '.join(remedial_topics[:3])}\n\n"
                    f"Please speak with the class teacher for a detailed plan.\n"
                    f"— School OS Academic Alert"
                )
            else:
                message = (
                    f"Dear Parent,\n\n"
                    f"A mild dip in your child's performance has been detected "
                    f"in: {', '.join(weak_subjects)}.\n\n"
                    f"Encouraging extra practice at home will help.\n"
                    f"— School OS"
                )

            queued = await self.queue_notification(
                recipient_id       = parent_id,
                channel            = "whatsapp",
                notification_type  = "academic_alert",
                payload            = {
                    "message":      message,
                    "risk_level":   risk_level,
                    "student_id":   self.student_id,
                    "weak_subjects": weak_subjects,
                }
            )
            if queued:
                notifications_queued += 1
            else:
                logger.error(
                    f"[AcademicAgent] Failed to queue parent alert "
                    f"for student_id={self.student_id} parent_id={parent_id}"
                )

        # ── Save updated agent state ─────────────────────────────────
        await self.save_state(
            entity_id   = self.student_id,
            entity_type = "student",
            state       = {
                "risk_level":       risk_level,
                "last_alert_date":  str(date.today()),
                "alerted_count":    1,   # Phase 5 cron will increment this
                "weak_subjects":    weak_subjects,
                "last_summary":     summary,
                "remedial_topics":  remedial_topics,
            }
        )

        logger.info(
            f"[AcademicAgent] student_id={self.student_id} "
            f"risk={risk_level} notifications_queued={notifications_queued}"
        )

        return {
            "result":               "alert_sent" if notifications_queued else "queue_failed",
            "risk_level":           risk_level,
            "weak_subjects":        weak_subjects,
            "notifications_queued": notifications_queued,
        }
