# backend/app/agents/admin_workflow_agent.py

import json
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.attendance import Attendance, AttendanceStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.models.class_ import Class_

logger = logging.getLogger(__name__)


class AdminWorkflowAgent(BaseAgent):
    """
    Automates routine admin tasks daily.

    Cron:  Daily at 7 AM

    Tasks automated:
        1. Detect absent teachers → suggest substitute assignments
        2. Generate daily attendance summary report for admin
        3. Flag classes with no attendance marked (teacher may be absent)
        4. Send morning briefing to admin
    """

    def __init__(self, school_id: int):
        super().__init__("admin_workflow_agent", school_id)

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            today = date.today()

            # Get all classes
            classes = db.query(Class_).filter(
                Class_.school_id == self.school_id
            ).all()

            # Check which classes have attendance marked today
            classes_with_attendance = set()
            today_att = db.query(Attendance).filter(
                Attendance.school_id == self.school_id,
                Attendance.date      == today,
            ).all()

            for att in today_att:
                classes_with_attendance.add(att.class_id)

            classes_without_attendance = [
                c for c in classes
                if c.id not in classes_with_attendance
            ]

            # Yesterday's attendance summary
            yesterday = today - timedelta(days=1)
            yesterday_att = db.query(Attendance).filter(
                Attendance.school_id == self.school_id,
                Attendance.date      == yesterday,
            ).all()

            total_students = db.query(Student).filter(
                Student.school_id == self.school_id,
                Student.is_active == True,
            ).count()

            yesterday_present = sum(
                1 for a in yesterday_att
                if a.status == AttendanceStatus.present
            )
            yesterday_absent = sum(
                1 for a in yesterday_att
                if a.status == AttendanceStatus.absent
            )

            # Get all teachers for admin context
            teachers = db.query(User).filter(
                User.school_id == self.school_id,
                User.role      == UserRole.teacher,
                User.is_active == True,
            ).all()

            # Get admin users
            admins = db.query(User).filter(
                User.school_id == self.school_id,
                User.role      == UserRole.admin,
                User.is_active == True,
            ).all()

            prev_state = await self.load_state(self.school_id, "school")

            return {
                "today":                     str(today),
                "total_classes":             len(classes),
                "classes_without_attendance": [
                    {"id": c.id, "name": c.display_name}
                    for c in classes_without_attendance
                ],
                "yesterday_present":         yesterday_present,
                "yesterday_absent":          yesterday_absent,
                "total_students":            total_students,
                "teacher_count":             len(teachers),
                "admin_ids":                 [a.id for a in admins],
                "prev_state":                prev_state,
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        missing_att = data["classes_without_attendance"]
        yesterday_absent_rate = (
            round((data["yesterday_absent"] / data["total_students"]) * 100, 1)
            if data["total_students"] > 0 else 0
        )

        # Generate briefing using LLM
        prompt = f"""
Generate a concise morning briefing for a school admin/principal.

Date:            {data['today']}
Total classes:   {data['total_classes']}
Classes without attendance today: {len(missing_att)}
Yesterday — Present: {data['yesterday_present']}, Absent: {data['yesterday_absent']}
Absence rate yesterday: {yesterday_absent_rate}%

Generate a brief, actionable morning briefing. Return JSON only:
{{
  "greeting": "Good morning! Here is your school briefing for {data['today']}.",
  "highlights": [
    "Highlight 1 (e.g. attendance status)",
    "Highlight 2",
    "Highlight 3"
  ],
  "action_items": [
    "Action item 1 (specific and actionable)",
    "Action item 2"
  ],
  "overall_status": "Normal" | "Attention Needed" | "Urgent"
}}
"""
        text, cost = await safe_llm_call(
            prompt=prompt,
            model="gemini-2.0-flash",
            max_tokens=400,
            expect_json=True,
        )
        self._add_cost(cost)

        try:
            briefing = json.loads(text)
        except json.JSONDecodeError:
            briefing = {
                "greeting":       f"Good morning! Today is {data['today']}.",
                "highlights":     [],
                "action_items":   [],
                "overall_status": "Normal",
            }

        return {
            "briefing":          briefing,
            "missing_att_count": len(missing_att),
            "missing_classes":   missing_att,
            "admin_ids":         data["admin_ids"],
            "yesterday_absent_rate": yesterday_absent_rate,
        }

    async def decide(self, analysis: dict) -> dict:
        return {"action": "send_briefing", "analysis": analysis}

    async def act(self, decision: dict) -> dict:
        analysis = decision["analysis"]
        briefing = analysis["briefing"]
        admin_ids = analysis["admin_ids"]

        if not admin_ids:
            return {"result": "no_admins_found"}

        missing = analysis["missing_classes"]
        missing_text = (
            "\n\nClasses without attendance today:\n" +
            "\n".join(f"• {c['name']}" for c in missing)
            if missing else ""
        )

        action_text = (
            "\n\nToday's action items:\n" +
            "\n".join(
                f"{i+1}. {a}"
                for i, a in enumerate(briefing.get("action_items", []))
            )
            if briefing.get("action_items") else ""
        )

        message = (
            f"{briefing.get('greeting', 'Good morning!')}\n\n"
            f"Status: {briefing.get('overall_status', 'Normal')}\n\n"
            + "\n".join(f"• {h}" for h in briefing.get("highlights", []))
            + missing_text
            + action_text
            + "\n\n— School OS Admin Assistant"
        )

        sent = 0
        for admin_id in admin_ids:
            await self.queue_notification(
                recipient_id      = admin_id,
                channel           = "email",
                notification_type = "admin_morning_briefing",
                payload           = {
                    "message":        message,
                    "overall_status": briefing.get("overall_status"),
                    "missing_att_count": analysis["missing_att_count"],
                }
            )
            sent += 1

        await self.save_state(
            self.school_id, "school",
            {
                "last_briefing_date":     str(date.today()),
                "last_absence_rate":      analysis["yesterday_absent_rate"],
                "last_missing_att_count": analysis["missing_att_count"],
            }
        )

        return {
            "result":       "briefing_sent",
            "admins_notified": sent,
            "overall_status": briefing.get("overall_status"),
        }
