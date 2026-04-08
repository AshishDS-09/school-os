# backend/app/agents/base_agent.py

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.agent_log import AgentLog, AgentOutcome
from app.models.agent_state import AgentState
from app.models.notif_queue import NotificationQueue, QueueStatus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all 10 School OS agents.

    Every agent follows the same 4-step lifecycle:
        fetch_data()  →  analyze()  →  decide()  →  act()

    Shared behaviour (logging, state, notifications) lives here.
    Subclasses only implement the 4 abstract methods.

    Usage:
        class MyAgent(BaseAgent):
            def __init__(self, school_id, student_id):
                super().__init__("my_agent", school_id)
                self.student_id = student_id

            async def fetch_data(self): ...
            async def analyze(self, data): ...
            async def decide(self, analysis): ...
            async def act(self, decision): ...
    """

    def __init__(self, agent_name: str, school_id: int):
        self.agent_name  = agent_name
        self.school_id   = school_id
        self.start_time  = datetime.utcnow()
        self.logger      = logging.getLogger(f"agents.{agent_name}")
        self._cost_usd   = 0.0   # accumulated Gemini cost for this run

    # ── Abstract lifecycle methods ────────────────────────────────────
    # Every subclass MUST implement all four

    @abstractmethod
    async def fetch_data(self) -> dict:
        """
        Step 1 — Pull all data the agent needs from PostgreSQL.
        Also loads previous agent_state here.
        Must return a dict.
        """

    @abstractmethod
    async def analyze(self, data: dict) -> dict:
        """
        Step 2 — Analyse the data. May call Gemini.
        Must return a dict with at minimum a 'risk_level' key.
        """

    @abstractmethod
    async def decide(self, analysis: dict) -> dict:
        """
        Step 3 — Decide what action to take.
        Must return a dict with at minimum an 'action' key.
        e.g. {'action': 'send_alert'} or {'action': 'skip'}
        """

    @abstractmethod
    async def act(self, decision: dict) -> dict:
        """
        Step 4 — Execute the decision.
        Queue notifications, update DB records, save state.
        Must return a dict describing what was done.
        """

    # ── Main entry point ──────────────────────────────────────────────

    async def run(self) -> dict:
        """
        Orchestrates the full lifecycle: fetch → analyze → decide → act.
        Called by Celery tasks. Always logs the result — success or error.
        Returns the outcome dict from act().
        """
        self.logger.info(
            f"Starting {self.agent_name} for school_id={self.school_id}"
        )
        outcome = {}
        error   = None

        try:
            data     = await self.fetch_data()
            analysis = await self.analyze(data)
            decision = await self.decide(analysis)
            outcome  = await self.act(decision)

            self.logger.info(
                f"{self.agent_name} completed: action={decision.get('action')} "
                f"outcome={outcome}"
            )

        except Exception as e:
            error = str(e)
            self.logger.error(
                f"{self.agent_name} failed: {error}", exc_info=True
            )
            # Re-raise so Celery can retry if configured
            raise

        finally:
            # Always log — even on error
            await self._log_run(
                outcome=outcome,
                error=error
            )

        return outcome

    # ── State persistence ─────────────────────────────────────────────

    async def load_state(self, entity_id: int, entity_type: str) -> dict:
        """
        Load the previous run's state for this entity from agent_state table.
        Returns empty dict if first time running for this entity.

        Example return value for academic_agent + student_42:
        {
            "risk_level":       "HIGH",
            "last_alert_date":  "2024-11-10",
            "alerted_count":    2,
            "weak_subjects":    ["Mathematics", "Science"]
        }
        """
        db: Session = SessionLocal()
        try:
            state = db.query(AgentState).filter(
                AgentState.agent_name  == self.agent_name,
                AgentState.entity_id   == entity_id,
                AgentState.entity_type == entity_type,
                AgentState.school_id   == self.school_id,
            ).first()
            return state.state_json if state else {}
        finally:
            db.close()

    async def save_state(
        self,
        entity_id: int,
        entity_type: str,
        state: dict
    ) -> None:
        """
        Persist state to agent_state table so the next run remembers it.
        Upserts: creates if not exists, updates if it does.
        """
        db: Session = SessionLocal()
        try:
            existing = db.query(AgentState).filter(
                AgentState.agent_name  == self.agent_name,
                AgentState.entity_id   == entity_id,
                AgentState.entity_type == entity_type,
                AgentState.school_id   == self.school_id,
            ).first()

            if existing:
                existing.state_json = state
                existing.last_run   = datetime.utcnow()
            else:
                db.add(AgentState(
                    agent_name  = self.agent_name,
                    school_id   = self.school_id,
                    entity_id   = entity_id,
                    entity_type = entity_type,
                    state_json  = state,
                    last_run    = datetime.utcnow(),
                ))
            db.commit()
        finally:
            db.close()

    # ── Notification queuing ──────────────────────────────────────────

    # backend/app/agents/base_agent.py
    # Replace queue_notification method with this updated version:

    async def queue_notification(
        self,
        recipient_id:      int,
        channel:           str,
        notification_type: str,
        payload:           dict,
    ) -> bool:
        """
        1. Writes to notification_queue  → Celery worker sends it
        2. Writes to notifications       → Admin sees it immediately
        """
        from app.models.notification import (
            Notification, NotificationChannel, NotificationStatus
        )

        channel_enum_map = {
            "whatsapp": NotificationChannel.whatsapp,
            "sms":      NotificationChannel.sms,
            "email":    NotificationChannel.email,
            "in_app":   NotificationChannel.in_app,
        }

        db: Session = SessionLocal()
        try:
            # 1. Write to queue for sending
            queue_item = NotificationQueue(
                school_id    = self.school_id,
                recipient_id = recipient_id,
                channel      = channel,
                payload      = {
                    "notification_type": notification_type,
                    **payload,
                },
                status = QueueStatus.pending,
            )
            db.add(queue_item)

            # 2. Write immediate record for admin visibility
            db.add(Notification(
                school_id         = self.school_id,
                recipient_id      = recipient_id,
                channel           = channel_enum_map.get(
                    channel, NotificationChannel.in_app
                ),
                content           = payload.get("message", ""),
                notification_type = notification_type,
                triggered_by      = self.agent_name,
                status            = NotificationStatus.pending,
            ))

            db.commit()

            self.logger.info(
                f"Queued {channel} notification for "
                f"recipient_id={recipient_id} type={notification_type}"
            )
            # Best-effort immediate dispatch so notifications can still send
            # even when celery-beat is unavailable. The queue flusher remains
            # as a safety net.
            try:
                from app.tasks.notification_tasks import send_notification
                send_notification.delay(
                    queue_id=queue_item.id,
                    recipient_id=recipient_id,
                    channel=channel,
                    payload=queue_item.payload,
                    school_id=self.school_id,
                )
            except Exception as exc:
                self.logger.warning(
                    f"Immediate notification dispatch failed for queue_id={queue_item.id}: {exc}"
                )
            return True

        except Exception as e:
            self.logger.error(f"Failed to queue notification: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    # ── Internal logging ──────────────────────────────────────────────

    async def _log_run(self, outcome: dict, error: str | None) -> None:
        """
        Write a record to agent_logs table.
        Called automatically at end of every run() — success or failure.
        """
        duration_ms = int(
            (datetime.utcnow() - self.start_time).total_seconds() * 1000
        )
        db: Session = SessionLocal()
        try:
            db.add(AgentLog(
                school_id    = self.school_id,
                agent_name   = self.agent_name,
                trigger      = "event",
                action_taken = str(outcome) if outcome else None,
                outcome      = AgentOutcome.error if error else AgentOutcome.success,
                error_message = error,
                duration_ms  = duration_ms,
                cost_usd     = self._cost_usd,
            ))
            db.commit()
        finally:
            db.close()

    def _add_cost(self, cost: float) -> None:
        """Call this after every Gemini API call to track spending."""
        self._cost_usd += cost
