# backend/app/agents/admission_agent.py

import json
import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.lead import Lead, LeadStatus

logger = logging.getLogger(__name__)

# Follow-up sequence timing
FOLLOW_UP_DELAYS = [1, 3, 7]   # days after lead creation for each follow-up
MAX_FOLLOW_UPS   = 3


class AdmissionLeadAgent(BaseAgent):
    """
    Qualifies new admission leads and runs an automated follow-up sequence.

    Triggered by:  lead.created event  (instant qualification)
    Cron:          every hour          (follow-up sequence timing)

    Sequence:
        Day 0  → Lead created  → Instant welcome message + qualification
        Day 1  → Follow-up 1  → School highlights + visit invite
        Day 3  → Follow-up 2  → Testimonial + urgency (limited seats)
        Day 7  → Follow-up 3  → Final offer + direct contact
        After 3 follow-ups → Stop automatically
    """

    def __init__(self, school_id: int, lead_id: int):
        super().__init__("admission_agent", school_id)
        self.lead_id = lead_id

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            lead = db.query(Lead).filter(
                Lead.id        == self.lead_id,
                Lead.school_id == self.school_id,
            ).first()

            if not lead:
                return {"error": "lead_not_found"}

            prev_state = await self.load_state(self.lead_id, "lead")

            days_since_created = (date.today() - lead.created_at.date()).days

            return {
                "lead":               lead,
                "lead_id":            lead.id,
                "parent_name":        lead.parent_name,
                "parent_phone":       lead.parent_phone,
                "child_name":         lead.child_name,
                "grade":              lead.applying_for_grade,
                "status":             lead.status.value,
                "follow_up_count":    lead.follow_up_count,
                "days_since_created": days_since_created,
                "prev_state":         prev_state,
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        if data.get("error"):
            return {"action": "skip", "reason": data["error"]}

        status           = data["status"]
        follow_up_count  = data["follow_up_count"]
        days_since       = data["days_since_created"]
        prev_state       = data["prev_state"]

        # Skip if already admitted, rejected, or lost
        if status in ("admitted", "rejected", "lost"):
            return {"action": "skip", "reason": f"lead_is_{status}"}

        # Skip if max follow-ups reached
        if follow_up_count >= MAX_FOLLOW_UPS:
            return {"action": "skip", "reason": "max_followups_reached"}

        # Determine which follow-up is due
        next_followup_idx = follow_up_count    # 0-indexed
        if next_followup_idx >= len(FOLLOW_UP_DELAYS):
            return {"action": "skip", "reason": "all_followups_sent"}

        days_required = FOLLOW_UP_DELAYS[next_followup_idx]

        # Is it time for the next follow-up?
        if days_since < days_required:
            return {
                "action":      "skip",
                "reason":      "not_yet_time",
                "days_left":   days_required - days_since,
                "next_followup": next_followup_idx + 1,
            }

        # Check we haven't already sent this follow-up today
        last_sent = prev_state.get("last_followup_date")
        if last_sent == str(date.today()):
            return {"action": "skip", "reason": "followup_sent_today"}

        return {
            "action":         "send_followup",
            "followup_number": next_followup_idx + 1,
            "data":           data,
        }

    async def decide(self, analysis: dict) -> dict:
        return analysis   # analysis already contains the decision

    async def act(self, decision: dict) -> dict:
        action = decision.get("action")

        if action == "skip":
            return {"result": "skipped", "reason": decision.get("reason")}

        followup_num = decision["followup_number"]
        data         = decision["data"]

        # Build personalised message per follow-up number
        parent_name = data["parent_name"]
        child_name  = data["child_name"]
        grade       = data["grade"]

        messages = {
            1: (
                f"Dear {parent_name},\n\n"
                f"Thank you for your interest in admitting {child_name} to Grade {grade}.\n\n"
                f"We would love to have you visit our school and experience our facilities. "
                f"Our teachers are dedicated to academic excellence and overall development.\n\n"
                f"Reply to this message or call us to schedule a free school tour.\n"
                f"— Admissions Team"
            ),
            2: (
                f"Dear {parent_name},\n\n"
                f"Following up on your admission inquiry for {child_name} (Grade {grade}).\n\n"
                f"Our school has limited seats available for this academic year. "
                f"We would not want {child_name} to miss out.\n\n"
                f"Schedule a visit this week — it takes just 30 minutes.\n"
                f"— Admissions Team"
            ),
            3: (
                f"Dear {parent_name},\n\n"
                f"This is our final follow-up regarding {child_name}'s admission to Grade {grade}.\n\n"
                f"If you have any questions or concerns, please reply directly or call us. "
                f"We are happy to answer any questions you have.\n\n"
                f"We hope to welcome {child_name} to our school family.\n"
                f"— Principal"
            ),
        }

        message = messages.get(followup_num, messages[1])

        # Queue WhatsApp to parent
        await self.queue_notification(
            recipient_id      = self.lead_id,   # lead has no user_id — use lead_id as ref
            channel           = "whatsapp",
            notification_type = "admission_followup",
            payload           = {
                "message":        message,
                "followup_number": followup_num,
                "lead_id":        self.lead_id,
                "parent_phone":   data["parent_phone"],
            }
        )

        # Update lead follow_up_count in DB
        db: Session = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == self.lead_id).first()
            if lead:
                lead.follow_up_count += 1
                lead.last_follow_up   = date.today()
                if lead.status == LeadStatus.new:
                    lead.status = LeadStatus.contacted
                db.commit()
        finally:
            db.close()

        await self.save_state(
            self.lead_id, "lead",
            {
                "last_followup_date":   str(date.today()),
                "followup_count":       followup_num,
                "last_followup_number": followup_num,
            }
        )

        logger.info(
            f"[AdmissionAgent] lead_id={self.lead_id} "
            f"followup #{followup_num} sent"
        )

        return {
            "result":         "followup_sent",
            "followup_number": followup_num,
            "lead_id":        self.lead_id,
        }