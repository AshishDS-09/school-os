# backend/app/agents/teacher_copilot_agent.py

import json
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.marks import Marks
from app.models.class_ import Class_
from app.models.user import User

logger = logging.getLogger(__name__)


class TeacherCopilotAgent(BaseAgent):
    """
    Proactively suggests revision topics to teachers based on
    class-wide performance data. Runs before major exams.

    Triggered by:  Manual teacher request via API (instant)
    Cron:          1st of every month (proactive suggestions)

    This agent does NOT replace the API endpoints in teacher_tools.py.
    Those endpoints let teachers request content on demand.
    This agent proactively pushes suggestions to teachers.
    """

    def __init__(self, school_id: int, class_id: int, teacher_id: int):
        super().__init__("teacher_copilot_agent", school_id)
        self.class_id   = class_id
        self.teacher_id = teacher_id

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            class_  = db.query(Class_).filter(
                Class_.id        == self.class_id,
                Class_.school_id == self.school_id,
            ).first()

            teacher = db.query(User).filter(
                User.id == self.teacher_id
            ).first()

            # Get recent marks for the whole class
            from app.models.student import Student
            students = db.query(Student).filter(
                Student.class_id  == self.class_id,
                Student.school_id == self.school_id,
                Student.is_active == True,
            ).all()

            student_ids = [s.id for s in students]

            marks = db.query(Marks).filter(
                Marks.student_id.in_(student_ids),
                Marks.school_id == self.school_id,
            ).order_by(Marks.exam_date.desc()).limit(200).all()

            # Aggregate: subject → list of percentages
            subject_scores: dict[str, list[float]] = {}
            for m in marks:
                subject_scores.setdefault(m.subject, []).append(m.percentage)

            prev_state = await self.load_state(self.class_id, "class")

            return {
                "class_name":     class_.display_name if class_ else "Unknown",
                "teacher_id":     self.teacher_id,
                "student_count":  len(students),
                "subject_scores": subject_scores,
                "prev_state":     prev_state,
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        if not data["subject_scores"]:
            return {"has_suggestions": False}

        # Calculate class average per subject
        subject_avgs = {
            subj: round(sum(scores) / len(scores), 1)
            for subj, scores in data["subject_scores"].items()
        }

        # Find weak subjects (class average below 60%)
        weak_subjects = {
            subj: avg
            for subj, avg in subject_avgs.items()
            if avg < 60
        }

        if not weak_subjects:
            return {
                "has_suggestions": False,
                "subject_avgs":    subject_avgs,
            }

        prompt = f"""
You are an educational advisor for an Indian school.

Class:           {data['class_name']}
Students:        {data['student_count']}
Subject averages: {json.dumps(subject_avgs)}
Weak subjects (below 60%): {json.dumps(weak_subjects)}

Generate actionable suggestions for the teacher.
Return JSON only:
{{
  "weak_subjects": [
    {{
      "subject":          "subject name",
      "class_average":    65.0,
      "priority":         "HIGH" | "MEDIUM",
      "likely_weak_topics": ["topic1", "topic2"],
      "suggested_actions": [
        "Action 1 for teacher",
        "Action 2"
      ],
      "revision_plan": "Brief 2-week revision plan"
    }}
  ],
  "overall_summary": "One paragraph summary for the teacher"
}}
"""
        text, cost = await safe_llm_call(
            prompt=prompt,
            model="gpt-4o-mini",
            max_tokens=800,
            expect_json=True,
        )
        self._add_cost(cost)

        try:
            result = json.loads(text)
            result["has_suggestions"] = True
            result["subject_avgs"]    = subject_avgs
            return result
        except json.JSONDecodeError:
            return {"has_suggestions": False}

    async def decide(self, analysis: dict) -> dict:
        if not analysis.get("has_suggestions"):
            return {"action": "skip", "reason": "class_performing_well"}

        prev_state    = analysis.get("prev_state", {})
        last_notified = prev_state.get("last_notified_date")

        # Don't notify same teacher more than once per week
        from datetime import timedelta
        if last_notified:
            days_since = (date.today() - date.fromisoformat(last_notified)).days
            if days_since < 7:
                return {"action": "skip", "reason": "notified_recently"}

        return {"action": "notify_teacher", "analysis": analysis}

    async def act(self, decision: dict) -> dict:
        if decision["action"] == "skip":
            return {"result": "skipped", "reason": decision.get("reason")}

        analysis       = decision["analysis"]
        weak_subjects  = analysis.get("weak_subjects", [])
        summary        = analysis.get("overall_summary", "")

        if not weak_subjects:
            return {"result": "no_weak_subjects"}

        subject_list = ", ".join(
            f"{s['subject']} ({s['class_average']}%)" for s in weak_subjects
        )
        message = (
            f"Class Performance Alert\n\n"
            f"Weak subjects detected: {subject_list}\n\n"
            f"{summary}\n\n"
            f"Log in to School OS to view the detailed revision plan.\n"
            f"— School OS AI"
        )

        await self.queue_notification(
            recipient_id      = self.teacher_id,
            channel           = "email",
            notification_type = "teacher_copilot_suggestion",
            payload           = {
                "message":       message,
                "weak_subjects": weak_subjects,
                "class_id":      self.class_id,
            }
        )

        await self.save_state(
            self.class_id, "class",
            {
                "last_notified_date": str(date.today()),
                "weak_subjects":      [s["subject"] for s in weak_subjects],
            }
        )

        return {"result": "teacher_notified", "weak_subjects_count": len(weak_subjects)}