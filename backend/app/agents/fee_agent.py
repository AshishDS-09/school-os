# backend/app/agents/fee_agent.py

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.models.fee import FeeRecord, FeeStatus
from app.models.student import Student
from app.models.user import User

logger = logging.getLogger(__name__)

# Reminder sequence — days before/after due date
FIRST_REMINDER_DAYS_BEFORE  = 5   # 5 days before due date
SECOND_REMINDER_DAY_OF      = 0   # on the due date itself
ESCALATION_DAYS_OVERDUE     = 7   # escalate if overdue 7+ days
MAX_REMINDERS               = 4   # stop after 4 reminders


class FeeCollectionAgent(BaseAgent):
    """
    Manages fee payment reminders and overdue escalation.

    Triggered by:  fee.overdue event  OR  daily 8 AM cron
    Cron:          8 AM every day — scans all schools for due/overdue fees

    Reminder sequence:
        5 days before due  →  Reminder 1: friendly advance notice
        On due date        →  Reminder 2: today is due
        7 days overdue     →  Reminder 3: urgent — please pay
        14 days overdue    →  Reminder 4: final notice — escalate to admin
    """

    def __init__(self, school_id: int, student_id: int, fee_id: Optional[int] = None):
        super().__init__("fee_agent", school_id)
        self.student_id = student_id
        self.fee_id     = fee_id

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            student = db.query(Student).filter(
                Student.id        == self.student_id,
                Student.school_id == self.school_id,
            ).first()

            if not student:
                return {"error": "student_not_found"}

            parent = db.query(User).filter(
                User.id == student.parent_id
            ).first() if student.parent_id else None

            # Get all unpaid fee records for this student
            query = db.query(FeeRecord).filter(
                FeeRecord.student_id == self.student_id,
                FeeRecord.school_id  == self.school_id,
                FeeRecord.status.in_([FeeStatus.due, FeeStatus.overdue, FeeStatus.partial]),
            )
            if self.fee_id:
                query = query.filter(FeeRecord.id == self.fee_id)

            fees = query.all()

            prev_state = await self.load_state(self.student_id, "student")

            return {
                "student_name": student.full_name,
                "parent_id":    parent.id    if parent else None,
                "parent_phone": parent.phone if parent else None,
                "fees":         fees,
                "today":        date.today(),
                "prev_state":   prev_state,
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        if data.get("error"):
            return {"action_needed": False}

        fees  = data["fees"]
        today = data["today"]

        if not fees:
            return {"action_needed": False, "reason": "no_unpaid_fees"}

        actions = []
        for fee in fees:
            days_until_due  = (fee.due_date - today).days
            days_overdue    = (today - fee.due_date).days if today > fee.due_date else 0
            reminder_count  = fee.reminder_count

            # Determine which reminder to send
            if reminder_count >= MAX_REMINDERS:
                continue   # already sent max reminders — stop

            if days_overdue >= 14 and reminder_count == 3:
                urgency = "final_notice"
            elif days_overdue >= 7 and reminder_count <= 2:
                urgency = "urgent"
            elif days_until_due == 0 and reminder_count <= 1:
                urgency = "due_today"
            elif 1 <= days_until_due <= 5 and reminder_count == 0:
                urgency = "advance_notice"
            else:
                continue   # not time for a reminder yet

            actions.append({
                "fee_id":          fee.id,
                "fee_type":        fee.fee_type.value,
                "amount":          fee.amount,
                "balance_due":     fee.balance_due,
                "due_date":        str(fee.due_date),
                "days_overdue":    days_overdue,
                "days_until_due":  days_until_due,
                "urgency":         urgency,
                "reminder_count":  reminder_count,
            })

        return {
            "action_needed": len(actions) > 0,
            "actions":       actions,
            "prev_state":    data["prev_state"],
        }

    async def decide(self, analysis: dict) -> dict:
        if not analysis.get("action_needed"):
            return {"action": "skip", "reason": analysis.get("reason", "no_action_needed")}

        return {
            "action":  "send_reminders",
            "actions": analysis.get("actions", []),
        }

    async def act(self, decision: dict) -> dict:
        action = decision.get("action")

        if action == "skip":
            return {"result": "skipped"}

        actions    = decision.get("actions", [])
        parent_id  = None
        notifs     = 0

        db: Session = SessionLocal()
        try:
            student   = db.query(Student).filter(Student.id == self.student_id).first()
            parent_id = student.parent_id if student else None
        finally:
            db.close()

        for action_item in actions:
            urgency     = action_item["urgency"]
            balance_due = action_item["balance_due"]
            due_date    = action_item["due_date"]
            fee_type    = action_item["fee_type"].replace("_", " ").title()

            # Build message based on urgency
            if urgency == "advance_notice":
                message = (
                    f"Dear Parent,\n\n"
                    f"Reminder: {fee_type} fee of ₹{balance_due:,.0f} is due on "
                    f"{due_date}.\nPlease arrange payment in advance to avoid late fees.\n"
                    f"— School Accounts"
                )
            elif urgency == "due_today":
                message = (
                    f"Dear Parent,\n\n"
                    f"Today is the last date to pay {fee_type} fee of "
                    f"₹{balance_due:,.0f}.\n"
                    f"Please pay today to avoid a late fee penalty.\n"
                    f"— School Accounts"
                )
            elif urgency == "urgent":
                days_late = action_item["days_overdue"]
                message = (
                    f"Dear Parent,\n\n"
                    f"Your {fee_type} fee of ₹{balance_due:,.0f} is now "
                    f"{days_late} days overdue.\n"
                    f"Please clear it immediately or contact the school office "
                    f"to discuss an installment plan.\n"
                    f"— School Accounts"
                )
            else:  # final_notice
                message = (
                    f"Dear Parent,\n\n"
                    f"FINAL NOTICE: {fee_type} fee of ₹{balance_due:,.0f} is "
                    f"significantly overdue.\n"
                    f"Please contact the school office immediately. Failure to pay "
                    f"may affect your child's exam admission.\n"
                    f"— School Principal"
                )

            # Queue WhatsApp to parent
            if parent_id:
                await self.queue_notification(
                    recipient_id      = parent_id,
                    channel           = "whatsapp",
                    notification_type = "fee_reminder",
                    payload           = {
                        "message":   message,
                        "urgency":   urgency,
                        "fee_id":    action_item["fee_id"],
                        "amount":    balance_due,
                        "student_id": self.student_id,
                    }
                )
                notifs += 1

            # Increment reminder_count on the fee record
            db: Session = SessionLocal()
            try:
                fee = db.query(FeeRecord).filter(
                    FeeRecord.id == action_item["fee_id"]
                ).first()
                if fee:
                    fee.reminder_count += 1
                    if action_item["days_overdue"] > 0:
                        fee.status = FeeStatus.overdue
                    db.commit()
            finally:
                db.close()

        await self.save_state(
            self.student_id, "student",
            {
                "last_reminder_date": str(date.today()),
                "reminders_sent":     notifs,
            }
        )

        logger.info(
            f"[FeeAgent] student_id={self.student_id} "
            f"reminders_sent={notifs}"
        )

        return {"result": "reminders_sent", "count": notifs}