# backend/app/agents/parent_comm_agent.py

import json
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.user import User
from app.models.notif_queue import NotificationQueue, QueueStatus

logger = logging.getLogger(__name__)

# Supported Indian languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "gu": "Gujarati",
    "bn": "Bengali",
}


class ParentCommunicationAgent(BaseAgent):
    """
    Routes and translates notifications to parents in their preferred language.

    Triggered by: Any queued notification with language preference set
    Cron:         Every 15 minutes — processes pending queue

    This agent sits BETWEEN the notification queue and the actual
    Twilio sender. It intercepts messages, translates them if needed,
    and then marks them ready for the notification worker to send.

    Language flow:
        English message queued → agent reads parent's language preference
        → if 'hi' → translate to Hindi via GPT-4o-mini
        → update queue payload with translated message
        → notification worker sends translated message
    """

    def __init__(self, school_id: int):
        super().__init__("parent_comm_agent", school_id)

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            # Find pending notifications for this school
            # that may need translation
            pending = db.query(NotificationQueue).filter(
                NotificationQueue.school_id == self.school_id,
                NotificationQueue.status    == QueueStatus.pending,
            ).limit(20).all()

            # For each, get recipient's language preference
            items = []
            for notif in pending:
                parent = db.query(User).filter(
                    User.id == notif.recipient_id
                ).first()

                lang = parent.language if parent else "en"
                items.append({
                    "notif_id":    notif.id,
                    "recipient_id": notif.recipient_id,
                    "language":    lang,
                    "payload":     notif.payload,
                    "channel":     notif.channel,
                    "needs_translation": lang != "en",
                })

            return {"items": items}
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        items = data["items"]

        # Only process items that need translation
        to_translate = [i for i in items if i["needs_translation"]]

        if not to_translate:
            return {"translations_needed": 0, "items": []}

        translated = []
        for item in to_translate:
            message     = item["payload"].get("message", "")
            lang_code   = item["language"]
            lang_name   = SUPPORTED_LANGUAGES.get(lang_code, "Hindi")

            if not message:
                continue

            prompt = f"""
Translate this school notification message from English to {lang_name}.

Keep the same professional tone. Keep names, numbers, dates, and amounts unchanged.
Do not add any explanation or preamble — return ONLY the translated message.

English:
{message}
"""
            translated_text, cost = await safe_llm_call(
                prompt=prompt,
                model="gemini-2.0-flash",
                max_tokens=500,
                temperature=0.1,
                expect_json=False,
            )
            self._add_cost(cost)

            translated.append({
                **item,
                "translated_message": translated_text.strip(),
            })

        return {
            "translations_needed": len(to_translate),
            "translated":          translated,
        }

    async def decide(self, analysis: dict) -> dict:
        if analysis["translations_needed"] == 0:
            return {"action": "skip", "reason": "no_translation_needed"}

        return {"action": "update_queue", "analysis": analysis}

    async def act(self, decision: dict) -> dict:
        if decision["action"] == "skip":
            return {"result": "skipped"}

        analysis   = decision["analysis"]
        translated = analysis["translated"]
        updated    = 0

        db: Session = SessionLocal()
        try:
            for item in translated:
                notif = db.query(NotificationQueue).filter(
                    NotificationQueue.id == item["notif_id"]
                ).first()

                if not notif:
                    continue

                # Update payload with translated message
                updated_payload = {
                    **notif.payload,
                    "message":              item["translated_message"],
                    "original_message":     notif.payload.get("message"),
                    "translated_to":        item["language"],
                }
                notif.payload = updated_payload
                updated += 1

            db.commit()
        finally:
            db.close()

        logger.info(
            f"[ParentCommAgent] Translated {updated} messages "
            f"for school_id={self.school_id}"
        )

        return {
            "result":    "translations_applied",
            "count":     updated,
        }
