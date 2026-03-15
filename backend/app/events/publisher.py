
# backend/app/events/publisher.py

import json
import asyncio
import logging
from datetime import datetime
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Shared async Redis client ────────────────────────────────────────
# We use a single client across the entire app lifetime
_publisher_client: aioredis.Redis | None = None


async def get_publisher() -> aioredis.Redis:
    """
    Returns the shared Redis publisher client.
    Creates it on first call (lazy initialisation).
    """
    global _publisher_client
    if _publisher_client is None:
        _publisher_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return _publisher_client


async def publish_event(channel: str, payload: dict[str, Any]) -> None:
    """
    Publish an event to a Redis Pub/Sub channel.

    Call this from any API route AFTER the database write succeeds.
    Never call it before — if the DB write fails and you already
    published the event, the agent will act on data that doesn't exist.

    Args:
        channel:  Event name e.g. "marks.entered", "attendance.marked"
        payload:  Dict with event data. Must include school_id.

    Example:
        await publish_event("marks.entered", {
            "school_id":  1,
            "student_id": 42,
            "subject":    "Mathematics",
            "score":      45.0,
            "max_score":  100.0,
        })
    """
    try:
        client = await get_publisher()

        message = json.dumps({
            "channel":   channel,
            "school_id": payload.get("school_id"),
            "data":      payload,
            "timestamp": datetime.utcnow().isoformat(),
            "version":   "1.0",
        })

        # Publish to the channel — all subscribers receive this instantly
        subscribers_count = await client.publish(channel, message)

        logger.debug(
            f"Event published: channel={channel} "
            f"school_id={payload.get('school_id')} "
            f"subscribers={subscribers_count}"
        )

    except Exception as e:
        # IMPORTANT: never let event publishing crash the API route.
        # The database write already succeeded — that's what matters.
        # Events are best-effort.
        logger.warning(f"Failed to publish event '{channel}': {e}")


def publish_event_sync(channel: str, payload: dict[str, Any]) -> None:
    """
    Synchronous wrapper for publish_event.
    Use this when you're in a sync context (e.g. Celery task calling another event).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context — schedule as a task
            asyncio.create_task(publish_event(channel, payload))
        else:
            loop.run_until_complete(publish_event(channel, payload))
    except Exception as e:
        logger.warning(f"Failed to publish event sync '{channel}': {e}")


# ── Event channel name constants ─────────────────────────────────────
# Define all channel names here so you never mistype them in routes.
# Import these constants instead of hardcoding strings.

class Events:
    MARKS_ENTERED       = "marks.entered"
    ATTENDANCE_MARKED   = "attendance.marked"
    FEE_OVERDUE         = "fee.overdue"
    ASSIGNMENT_MISSED   = "assignment.missed"
    INCIDENT_CREATED    = "incident.created"
    LEAD_CREATED        = "lead.created"
    LEAD_UPDATED        = "lead.updated"