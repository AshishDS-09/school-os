# backend/app/agents/behavioral_agent.py

import json
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.database import SessionLocal
from app.core.llm import safe_llm_call
from app.models.incident import Incident, IncidentSeverity
from app.models.student import Student

logger = logging.getLogger(__name__)

HIGH_RISK_INCIDENT_COUNT  = 3   # 3+ incidents in 30 days → HIGH
MEDIUM_RISK_INCIDENT_COUNT = 2


class BehavioralMonitorAgent(BaseAgent):
    """
    Detects behavioral incident patterns and recommends intervention.

    Triggered by:  incident.created event
    Cron:          weekly (Sunday night)

    Pattern detection:
        3+ incidents in 30 days  → HIGH  → flag bullying risk, suggest counselor
        2 incidents in 30 days   → MEDIUM → suggest teacher conversation
        1 incident               → LOW   → log only
        HIGH severity incident   → Always alert regardless of count
    """

    def __init__(self, school_id: int, student_id: int):
        super().__init__("behavioral_agent", school_id)
        self.student_id = student_id

    async def fetch_data(self) -> dict:
        db: Session = SessionLocal()
        try:
            student = db.query(Student).filter(
                Student.id        == self.student_id,
                Student.school_id == self.school_id,
            ).first()

            if not student:
                return {"error": "student_not_found"}

            since     = date.today() - timedelta(days=30)
            incidents = db.query(Incident).filter(
                Incident.student_id == self.student_id,
                Incident.school_id  == self.school_id,
                Incident.incident_date >= since,
                Incident.is_resolved == False,
            ).order_by(Incident.incident_date.desc()).all()

            incident_summary = [
                {
                    "type":        i.incident_type.value,
                    "severity":    i.severity.value,
                    "date":        str(i.incident_date),
                    "description": i.description[:100],
                }
                for i in incidents
            ]

            high_severity = any(
                i.severity == IncidentSeverity.high for i in incidents
            )

            prev_state = await self.load_state(self.student_id, "student")

            return {
                "student_name":     student.full_name,
                "parent_id":        student.parent_id,
                "incident_count":   len(incidents),
                "incidents":        incident_summary,
                "has_high_severity": high_severity,
                "prev_state":       prev_state,
            }
        finally:
            db.close()

    async def analyze(self, data: dict) -> dict:
        if data.get("error"):
            return {"risk_level": "NONE"}

        count       = data["incident_count"]
        high_sev    = data["has_high_severity"]
        prev_state  = data["prev_state"]

        # Determine risk level
        if count >= HIGH_RISK_INCIDENT_COUNT or high_sev:
            risk_level = "HIGH"
        elif count >= MEDIUM_RISK_INCIDENT_COUNT:
            risk_level = "MEDIUM"
        elif count == 1:
            risk_level = "LOW"
        else:
            return {"risk_level": "NONE"}

        # Don't re-alert if already at same risk level
        if prev_state.get("risk_level") == risk_level and not high_sev:
            return {
                "risk_level": risk_level,
                "skip":       True,
                "reason":     "already_at_this_risk_level",
            }

        # Use LLM to identify patterns in incidents
        if count >= 2:
            prompt = f"""
Analyze these behavioral incidents for a school student.
Student: {data['student_name']}
Incidents in last 30 days: {json.dumps(data['incidents'], indent=2)}

Identify patterns and recommend interventions.
Return JSON only:
{{
  "pattern_detected":    "bullying" | "emotional_distress" | "attention_seeking" | "other" | "none",
  "pattern_description": "Brief description of the pattern",
  "recommended_action":  "counseling" | "parent_meeting" | "teacher_observation" | "none",
  "urgency":             "immediate" | "this_week" | "this_month",
  "counselor_note":      "Brief note for the school counselor"
}}
"""
            text, cost = await safe_llm_call(
                prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=400,
                expect_json=True,
            )
            self._add_cost(cost)
            try:
                pattern_analysis = json.loads(text)
            except json.JSONDecodeError:
                pattern_analysis = {"pattern_detected": "other", "urgency": "this_week"}
        else:
            pattern_analysis = {"pattern_detected": "none", "urgency": "this_month"}

        return {
            "risk_level":       risk_level,
            "skip":             False,
            "incident_count":   count,
            "pattern_analysis": pattern_analysis,
            "parent_id":        data["parent_id"],
            "student_name":     data["student_name"],
            "has_high_severity": high_sev,
        }

    async def decide(self, analysis: dict) -> dict:
        if analysis.get("risk_level") == "NONE":
            return {"action": "skip", "reason": "no_incidents"}
        if analysis.get("skip"):
            return {"action": "skip", "reason": analysis.get("reason")}

        risk_level = analysis["risk_level"]
        urgency    = analysis.get("pattern_analysis", {}).get("urgency", "this_week")

        if risk_level == "HIGH" or urgency == "immediate":
            return {
                "action":          "alert_high",
                "analysis":        analysis,
                "notify_parent":   True,
                "flag_for_admin":  True,
            }
        if risk_level == "MEDIUM":
            return {
                "action":         "alert_medium",
                "analysis":       analysis,
                "notify_parent":  False,   # teacher conversation first
                "flag_for_admin": False,
            }
        return {"action": "log_only", "analysis": analysis}

    async def act(self, decision: dict) -> dict:
        action   = decision.get("action")
        analysis = decision.get("analysis", {})

        if action == "skip":
            return {"result": "skipped"}

        if action == "log_only":
            await self.save_state(
                self.student_id, "student",
                {"risk_level": "LOW", "last_check": str(date.today())}
            )
            return {"result": "logged"}

        risk_level = analysis.get("risk_level")
        parent_id  = analysis.get("parent_id")
        pattern    = analysis.get("pattern_analysis", {})
        student_name = analysis.get("student_name", "")

        if decision.get("notify_parent") and parent_id:
            if risk_level == "HIGH":
                message = (
                    f"Dear Parent,\n\n"
                    f"We need to speak with you regarding {student_name}'s "
                    f"recent behavior at school.\n\n"
                    f"There have been {analysis['incident_count']} behavioral "
                    f"incidents in the past 30 days that require attention.\n\n"
                    f"Please contact the school at your earliest convenience to "
                    f"schedule a meeting with the class teacher and counselor.\n"
                    f"— School Management"
                )
                await self.queue_notification(
                    recipient_id      = parent_id,
                    channel           = "whatsapp",
                    notification_type = "behavioral_alert",
                    payload           = {
                        "message":       message,
                        "risk_level":    risk_level,
                        "student_id":    self.student_id,
                        "incident_count": analysis["incident_count"],
                    }
                )

        await self.save_state(
            self.student_id, "student",
            {
                "risk_level":       risk_level,
                "last_alert_date":  str(date.today()),
                "incident_count":   analysis.get("incident_count", 0),
                "pattern_detected": pattern.get("pattern_detected"),
                "counselor_flagged": decision.get("flag_for_admin", False),
            }
        )

        return {
            "result":      "alert_sent",
            "risk_level":  risk_level,
            "pattern":     pattern.get("pattern_detected"),
        }