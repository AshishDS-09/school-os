# backend/app/agents/teacher_performance_agent.py

import json
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.marks import Marks
from app.models.attendance import Attendance, AttendanceStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.models.class_ import Class_

logger = logging.getLogger(__name__)


class TeacherPerformanceAgent(BaseAgent):
    """
    Generates monthly teaching effectiveness reports.

    Cron only:  1st of every month
    No event trigger — this is a scheduled analysis.

    IMPORTANT FRAMING: Always present as a growth and support tool,
    never as surveillance. Reports are sent to the teacher themselves,
    not to admin, unless the teacher's class is severely underperforming.

    Metrics analysed:
        - Class average marks vs school average
        - Assignment completion rate
        - Attendance rate in their class
        - Month-over-month trend
    """

    def __init__(self, school_id: int, teacher_id: int):
        super().__init__("teacher_performance_agent", school_id)
        self.teacher_id = teacher_id

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            teacher = db.query(User).filter(
                User.id        == self.teacher_id,
                User.school_id == self.school_id,
                User.role      == UserRole.teacher,
            ).first()

            if not teacher:
                return {"error": "teacher_not_found"}

            # Find classes this teacher teaches
            classes = db.query(Class_).filter(
                Class_.class_teacher_id == self.teacher_id,
                Class_.school_id        == self.school_id,
            ).all()

            if not classes:
                return {"error": "no_classes_assigned"}

            class_ids   = [c.id for c in classes]
            since       = date.today() - timedelta(days=30)

            # Get student IDs in teacher's classes
            students = db.query(Student).filter(
                Student.class_id.in_(class_ids),
                Student.school_id == self.school_id,
                Student.is_active == True,
            ).all()
            student_ids = [s.id for s in students]

            # Class marks in last 30 days
            marks = db.query(Marks).filter(
                Marks.student_id.in_(student_ids),
                Marks.school_id == self.school_id,
                Marks.exam_date >= since,
            ).all()

            class_avg = (
                round(sum(m.percentage for m in marks) / len(marks), 1)
                if marks else 0
            )

            # School-wide average for comparison
            all_marks = db.query(Marks).filter(
                Marks.school_id == self.school_id,
                Marks.exam_date >= since,
            ).all()
            school_avg = (
                round(sum(m.percentage for m in all_marks) / len(all_marks), 1)
                if all_marks else 0
            )

            # Attendance rate in teacher's classes
            att_records = db.query(Attendance).filter(
                Attendance.class_id.in_(class_ids),
                Attendance.school_id == self.school_id,
                Attendance.date >= since,
            ).all()
            present_count = sum(
                1 for a in att_records if a.status == AttendanceStatus.present
            )
            att_rate = (
                round((present_count / len(att_records)) * 100, 1)
                if att_records else 0
            )

            # Subject breakdown
            subject_avgs: dict[str, list[float]] = {}
            for m in marks:
                subject_avgs.setdefault(m.subject, []).append(m.percentage)
            subject_summary = {
                subj: round(sum(scores) / len(scores), 1)
                for subj, scores in subject_avgs.items()
            }

            prev_state = await self.load_state(self.teacher_id, "teacher")

            return {
                "teacher_name":   teacher.full_name,
                "teacher_id":     self.teacher_id,
                "class_names":    [c.display_name for c in classes],
                "student_count":  len(students),
                "class_avg":      class_avg,
                "school_avg":     school_avg,
                "att_rate":       att_rate,
                "subject_summary": subject_summary,
                "marks_count":    len(marks),
                "prev_state":     prev_state,
                "month":          date.today().strftime("%B %Y"),
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        if data.get("error"):
            return {"skip": True, "reason": data["error"]}

        class_avg   = data["class_avg"]
        school_avg  = data["school_avg"]
        att_rate    = data["att_rate"]
        prev_state  = data["prev_state"]
        prev_avg    = prev_state.get("last_class_avg", class_avg)

        trend = "improving" if class_avg > prev_avg else (
            "declining" if class_avg < prev_avg - 3 else "stable"
        )
        vs_school = class_avg - school_avg

        prompt = f"""
You are an educational consultant generating a monthly report for a teacher.
IMPORTANT: This is a growth support tool — use encouraging, constructive language.

Teacher:        {data['teacher_name']}
Classes:        {', '.join(data['class_names'])}
Month:          {data['month']}
Students:       {data['student_count']}

Class average marks:   {class_avg}%
School average marks:  {school_avg}%  (difference: {vs_school:+.1f}%)
Attendance rate:       {att_rate}%
Performance trend:     {trend}
Previous month avg:    {prev_avg}%

Subject-wise averages: {json.dumps(data['subject_summary'])}

Generate a supportive monthly report. Return JSON only:
{{
  "overall_rating":    "Excellent" | "Good" | "Needs Support",
  "strengths":         ["strength 1", "strength 2"],
  "growth_areas":      ["area 1", "area 2"],
  "suggested_actions": ["action 1", "action 2", "action 3"],
  "summary_message":   "Encouraging 2-3 sentence summary for the teacher",
  "highlight":         "One specific thing the teacher did well this month"
}}
"""
        text, cost = await safe_llm_call(
            prompt=prompt,
            model="gpt-4o-mini",
            max_tokens=600,
            expect_json=True,
        )
        self._add_cost(cost)

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            result = {
                "overall_rating":  "Good",
                "summary_message": "Report generated successfully.",
                "strengths":       [],
                "growth_areas":    [],
                "suggested_actions": [],
            }

        result.update({
            "skip":       False,
            "class_avg":  class_avg,
            "school_avg": school_avg,
            "att_rate":   att_rate,
            "trend":      trend,
            "data":       data,
        })
        return result

    async def decide(self, analysis: dict) -> dict:
        if analysis.get("skip"):
            return {"action": "skip", "reason": analysis.get("reason")}
        return {"action": "send_report", "analysis": analysis}

    async def act(self, decision: dict) -> dict:
        if decision["action"] == "skip":
            return {"result": "skipped"}

        analysis = decision["analysis"]
        data     = analysis["data"]

        rating   = analysis.get("overall_rating", "Good")
        summary  = analysis.get("summary_message", "")
        strengths = analysis.get("strengths", [])
        growth    = analysis.get("growth_areas", [])
        actions   = analysis.get("suggested_actions", [])

        message = (
            f"Your Monthly Teaching Report — {data['month']}\n\n"
            f"Overall: {rating}\n"
            f"Class average: {analysis['class_avg']}% "
            f"(School avg: {analysis['school_avg']}%)\n"
            f"Attendance rate: {analysis['att_rate']}%\n\n"
            f"{summary}\n\n"
            + (f"Strengths this month:\n" +
               "\n".join(f"• {s}" for s in strengths) + "\n\n"
               if strengths else "")
            + (f"Focus areas:\n" +
               "\n".join(f"• {a}" for a in growth) + "\n\n"
               if growth else "")
            + (f"Suggested actions:\n" +
               "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions))
               if actions else "")
            + "\n\n— School OS (Growth Support Tool)"
        )

        await self.queue_notification(
            recipient_id      = self.teacher_id,
            channel           = "email",
            notification_type = "teacher_performance_report",
            payload           = {
                "message":        message,
                "overall_rating": rating,
                "class_avg":      analysis["class_avg"],
                "month":          data["month"],
            }
        )

        await self.save_state(
            self.teacher_id, "teacher",
            {
                "last_report_date": str(date.today()),
                "last_class_avg":   analysis["class_avg"],
                "last_rating":      rating,
            }
        )

        return {"result": "report_sent", "rating": rating}