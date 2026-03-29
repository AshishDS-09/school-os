# backend/app/agents/learning_agent.py

import json
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.marks import Marks
from app.models.student import Student

logger = logging.getLogger(__name__)


class PersonalizedLearningAgent(BaseAgent):
    """
    Creates weekly personalised revision plans for each student.

    Cron only: Every Sunday at 8 PM
    No event trigger — this is a scheduled weekly analysis.

    Output:
        - Identifies each student's 2-3 weakest topics
        - Generates a 5-day personalised revision schedule
        - Suggests free online resources (YouTube, NCERT)
        - Sent to parent via WhatsApp every Sunday
    """

    def __init__(self, school_id: int, student_id: int):
        super().__init__("learning_agent", school_id)
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

            since = date.today() - timedelta(days=60)
            marks = db.query(Marks).filter(
                Marks.student_id == self.student_id,
                Marks.school_id  == self.school_id,
                Marks.exam_date  >= since,
            ).order_by(Marks.exam_date.desc()).all()

            # Group by subject with trend
            subject_data: dict[str, dict] = {}
            for m in marks:
                if m.subject not in subject_data:
                    subject_data[m.subject] = {"scores": [], "latest": 0}
                subject_data[m.subject]["scores"].append(m.percentage)
                subject_data[m.subject]["latest"] = m.percentage

            # Calculate average and trend per subject
            subject_summary = {}
            for subj, d in subject_data.items():
                scores = d["scores"]
                avg    = round(sum(scores) / len(scores), 1)
                trend  = "improving" if len(scores) >= 2 and scores[0] > scores[-1] else (
                    "declining" if len(scores) >= 2 and scores[0] < scores[-1] else "stable"
                )
                subject_summary[subj] = {
                    "average": avg,
                    "latest":  d["latest"],
                    "trend":   trend,
                    "exams":   len(scores),
                }

            # Sort by average ascending — weakest first
            weak_subjects = sorted(
                subject_summary.items(),
                key=lambda x: x[1]["average"]
            )[:3]   # top 3 weakest

            prev_state = await self.load_state(self.student_id, "student")

            return {
                "student_name":     student.full_name,
                "parent_id":        student.parent_id,
                "subject_summary":  subject_summary,
                "weak_subjects":    weak_subjects,
                "has_marks":        len(marks) > 0,
                "prev_state":       prev_state,
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        if data.get("error") or not data["has_marks"]:
            return {"skip": True, "reason": "no_data"}

        weak = data["weak_subjects"]
        if not weak or weak[0][1]["average"] >= 75:
            # All subjects above 75% — student is doing well
            return {"skip": True, "reason": "student_performing_well"}

        prev_state  = data["prev_state"]
        last_plan   = prev_state.get("last_plan_date")

        # Only generate once per week
        if last_plan:
            days_since = (date.today() - date.fromisoformat(last_plan)).days
            if days_since < 6:
                return {"skip": True, "reason": "plan_generated_recently"}

        weak_summary = {
            subj: details
            for subj, details in weak
            if details["average"] < 75
        }

        prompt = f"""
Create a personalised 5-day weekly revision plan for an Indian school student.

Student: {data['student_name']}
Weak subjects (average below 75%):
{json.dumps(weak_summary, indent=2)}

Create a practical, manageable plan. Return JSON only:
{{
  "student_name": "{data['student_name']}",
  "week_of": "{date.today().isoformat()}",
  "focus_subjects": ["subject1", "subject2"],
  "daily_plan": [
    {{
      "day":       "Monday",
      "subject":   "Mathematics",
      "topic":     "Specific topic to revise",
      "duration":  "30 minutes",
      "activity":  "What to do: e.g. solve 10 practice problems from chapter 5",
      "resource":  "NCERT Chapter 5 exercises / Khan Academy: [topic]"
    }},
    {{ "day": "Tuesday",  "subject": "...", "topic": "...", "duration": "...", "activity": "...", "resource": "..." }},
    {{ "day": "Wednesday","subject": "...", "topic": "...", "duration": "...", "activity": "...", "resource": "..." }},
    {{ "day": "Thursday", "subject": "...", "topic": "...", "duration": "...", "activity": "...", "resource": "..." }},
    {{ "day": "Friday",   "subject": "...", "topic": "...", "duration": "...", "activity": "...", "resource": "..." }}
  ],
  "weekend_tip": "One helpful tip for the weekend",
  "encouragement": "Short motivating message for the student"
}}
"""
        text, cost = await safe_llm_call(
            prompt=prompt,
            model="gpt-4o-mini",
            max_tokens=1000,
            expect_json=True,
        )
        self._add_cost(cost)

        try:
            plan = json.loads(text)
        except json.JSONDecodeError:
            return {"skip": True, "reason": "llm_parse_failed"}

        return {
            "skip":       False,
            "plan":       plan,
            "parent_id":  data["parent_id"],
            "weak_count": len(weak_summary),
        }

    async def decide(self, analysis: dict) -> dict:
        if analysis.get("skip"):
            return {"action": "skip", "reason": analysis.get("reason")}
        return {"action": "send_plan", "analysis": analysis}

    async def act(self, decision: dict) -> dict:
        if decision["action"] == "skip":
            return {"result": "skipped", "reason": decision.get("reason")}

        analysis  = decision["analysis"]
        plan      = analysis["plan"]
        parent_id = analysis["parent_id"]

        if not parent_id:
            return {"result": "no_parent_linked"}

        # Format daily plan into readable WhatsApp message
        daily_text = "\n".join(
            f"{d['day']}: {d['subject']} — {d['topic']} ({d['duration']})\n"
            f"  Task: {d['activity']}"
            for d in plan.get("daily_plan", [])
        )

        message = (
            f"Weekly Study Plan for {plan.get('student_name', 'Your Child')}\n"
            f"Week of {plan.get('week_of', str(date.today()))}\n\n"
            f"Focus subjects: {', '.join(plan.get('focus_subjects', []))}\n\n"
            f"{daily_text}\n\n"
            f"Weekend tip: {plan.get('weekend_tip', '')}\n\n"
            f"{plan.get('encouragement', 'Keep up the great work!')}\n\n"
            f"— School OS Learning Assistant"
        )

        await self.queue_notification(
            recipient_id      = parent_id,
            channel           = "whatsapp",
            notification_type = "learning_plan",
            payload           = {
                "message":       message,
                "plan":          plan,
                "student_id":    self.student_id,
            }
        )

        await self.save_state(
            self.student_id, "student",
            {
                "last_plan_date":    str(date.today()),
                "focus_subjects":    plan.get("focus_subjects", []),
                "plans_generated":   1,
            }
        )

        return {
            "result":       "plan_sent",
            "focus_subjects": plan.get("focus_subjects", []),
        }