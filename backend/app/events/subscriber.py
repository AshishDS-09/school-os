# # backend/app/events/subscriber.py

# import asyncio
# import redis.asyncio as aioredis
# import os

# async def listen():
#     print("Event subscriber starting...")
#     client = aioredis.from_url(
#         os.getenv("REDIS_URL", "redis://redis:6379/0")
#     )
#     pubsub = client.pubsub()
#     await pubsub.subscribe("marks.entered", "attendance.marked")
#     print("Subscribed to events. Waiting...")
#     async for message in pubsub.listen():
#         if message["type"] == "message":
#             print(f"Event received: {message['data']}")
#             # Agents will be routed here in Phase 4

# if __name__ == "__main__":
#     asyncio.run(listen())

# backend/app/events/subscriber.py

import asyncio
import json
import logging
import sys
import os

import redis.asyncio as aioredis

# Make sure Python can find the app module when run as: python -m app.events.subscriber
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.config import settings
from app.events.publisher import Events

# Set up logging so we can see events arriving in Docker logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EVENT-SUB] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# ── Event router ─────────────────────────────────────────────────────
# Maps each event channel to the Celery task that should handle it.
# We import tasks lazily (inside the function) to avoid circular imports.

async def route_event(channel: str, data: dict) -> None:
    """
    Decide which Celery task to run based on the event channel.
    Each task runs asynchronously in the background — this function
    returns immediately after calling .delay().
    """
    school_id  = data.get("school_id")
    event_data = data.get("data", {})

    logger.info(f"Routing event: channel={channel} school_id={school_id}")

    try:
        if channel == Events.MARKS_ENTERED:
            # Marks entered → run Academic Performance Agent for this student
            from app.tasks.agent_tasks import run_academic_agent_for_student
            student_id = event_data.get("student_id")
            if student_id and school_id:
                run_academic_agent_for_student.delay(
                    student_id=student_id,
                    school_id=school_id
                )
                logger.info(
                    f"Dispatched academic_agent for "
                    f"student_id={student_id} school_id={school_id}"
                )

        elif channel == Events.ATTENDANCE_MARKED:
            # Attendance marked → run Attendance Risk Agent
            from app.tasks.agent_tasks import run_attendance_agent_for_student
            student_id = event_data.get("student_id")
            if student_id and school_id:
                run_attendance_agent_for_student.delay(
                    student_id=student_id,
                    school_id=school_id
                )
                logger.info(
                    f"Dispatched attendance_agent for "
                    f"student_id={student_id} school_id={school_id}"
                )

        elif channel == Events.INCIDENT_CREATED:
            # Incident logged → run Behavioral Monitor Agent
            from app.tasks.agent_tasks import run_behavioral_agent_for_student
            student_id = event_data.get("student_id")
            if student_id and school_id:
                run_behavioral_agent_for_student.delay(
                    student_id=student_id,
                    school_id=school_id
                )
                logger.info(
                    f"Dispatched behavioral_agent for "
                    f"student_id={student_id} school_id={school_id}"
                )

        elif channel == Events.LEAD_CREATED:
            # New admission lead → run Admission Lead Agent
            from app.tasks.agent_tasks import run_admission_agent_for_lead
            lead_id = event_data.get("lead_id")
            if lead_id and school_id:
                run_admission_agent_for_lead.delay(
                    lead_id=lead_id,
                    school_id=school_id
                )
                logger.info(
                    f"Dispatched admission_agent for "
                    f"lead_id={lead_id} school_id={school_id}"
                )

        elif channel == Events.FEE_OVERDUE:
            # Fee overdue detected → run Fee Collection Agent
            from app.tasks.agent_tasks import run_fee_agent_for_student
            student_id = event_data.get("student_id")
            fee_id     = event_data.get("fee_id")
            if student_id and school_id:
                run_fee_agent_for_student.delay(
                    student_id=student_id,
                    fee_id=fee_id,
                    school_id=school_id
                )
                logger.info(
                    f"Dispatched fee_agent for "
                    f"student_id={student_id} school_id={school_id}"
                )

        else:
            # Unknown channel — log and ignore
            logger.warning(f"No handler for event channel: '{channel}'")

    except Exception as e:
        # Never crash the subscriber loop — just log the error and continue
        logger.error(f"Error routing event '{channel}': {e}", exc_info=True)


# ── Main listener loop ────────────────────────────────────────────────

async def listen() -> None:
    """
    Main entry point — connects to Redis and listens forever.

    This function runs in a loop:
    1. Connect to Redis
    2. Subscribe to all event channels
    3. For each message: parse JSON → route to correct Celery task
    4. If Redis disconnects: wait 5 seconds and reconnect automatically

    The reconnection logic means this service survives Redis restarts.
    """
    # All channels we want to listen to
    channels = [
        Events.MARKS_ENTERED,
        Events.ATTENDANCE_MARKED,
        Events.FEE_OVERDUE,
        Events.ASSIGNMENT_MISSED,
        Events.INCIDENT_CREATED,
        Events.LEAD_CREATED,
        Events.LEAD_UPDATED,
    ]

    logger.info("=" * 50)
    logger.info("School OS Event Subscriber starting...")
    logger.info(f"Connecting to Redis: {settings.REDIS_URL}")
    logger.info(f"Listening to channels: {channels}")
    logger.info("=" * 50)

    while True:  # outer loop: reconnect if Redis connection drops
        client  = None
        pubsub  = None

        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

            # Test the connection
            await client.ping()
            logger.info("Redis connected successfully")

            pubsub = client.pubsub()

            # Subscribe to all channels at once
            await pubsub.subscribe(*channels)
            logger.info(f"Subscribed to {len(channels)} channels. Waiting for events...")

            # Inner loop: process messages
            async for raw_message in pubsub.listen():
                # pubsub.listen() yields subscription confirmations too
                # We only care about actual data messages
                if raw_message["type"] != "message":
                    continue

                try:
                    # Parse the JSON payload
                    payload = json.loads(raw_message["data"])
                    channel = payload.get("channel", raw_message["channel"])

                    # Route to the correct agent task
                    await route_event(channel, payload)

                except json.JSONDecodeError as e:
                    logger.error(f"Could not parse event JSON: {e}")
                    logger.error(f"Raw data: {raw_message.get('data', '')[:200]}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue the loop — never let one bad message stop everything

        except asyncio.CancelledError:
            # Graceful shutdown (e.g. Docker stop signal)
            logger.info("Subscriber shutting down gracefully...")
            break

        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)  # wait before reconnecting

        finally:
            # Clean up connections
            try:
                if pubsub:
                    await pubsub.unsubscribe()
                    await pubsub.close()
                if client:
                    await client.close()
            except Exception:
                pass


def main():
    """Entry point when run as: python -m app.events.subscriber"""
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        logger.info("Subscriber stopped by user")


if __name__ == "__main__":
    main()