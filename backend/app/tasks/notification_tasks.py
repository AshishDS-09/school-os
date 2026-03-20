# backend/app/tasks/notification_tasks.py

import logging
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy.orm import Session

from app.tasks import celery_app
from app.core.database import SessionLocal
from app.models.notif_queue import NotificationQueue, QueueStatus
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.user import User

logger = logging.getLogger(__name__)

# Retry backoff: attempt 1 → wait 2 min, attempt 2 → 4 min, attempt 3 → 8 min
RETRY_BACKOFF = [120, 240, 480]
MAX_RETRIES   = 3


def _recipient_label(channel: str, recipient: User) -> str:
    """Log the destination that actually matches the delivery channel."""
    if channel in {"whatsapp", "sms"}:
        return recipient.phone or f"user_id={recipient.id}"
    if channel == "email":
        return recipient.email or f"user_id={recipient.id}"
    return f"user_id={recipient.id}"


# ══════════════════════════════════════════════════════════════════════
# MAIN SEND TASK
# ══════════════════════════════════════════════════════════════════════

@celery_app.task(
    name="send_notification",
    bind=True,
    max_retries=MAX_RETRIES,
    acks_late=True,          # only remove from queue after task succeeds
    queue="notifications",        # ← add this line
)
def send_notification(
    self,
    queue_id:    int,
    recipient_id: int,
    channel:     str,
    payload:     dict,
    school_id:   int,
):
    """
    Send a single notification via the specified channel.

    This task is called by the flush_notification_queue task below.
    Never call this directly from agents — agents call queue_notification()
    on BaseAgent which writes to notification_queue table.

    Flow:
        1. Load recipient phone/email from users table
        2. Call the correct channel function (WhatsApp / SMS / Email)
        3. On success: mark queue row as 'sent', write to notifications table
        4. On failure: increment retry_count, set next_retry_at, mark 'retrying'
        5. After MAX_RETRIES failures: mark as 'failed'
    """
    db: Session = SessionLocal()
    try:
        # Load the queue record
        queue_item = db.query(NotificationQueue).filter(
            NotificationQueue.id == queue_id
        ).first()

        if not queue_item:
            logger.warning(f"Queue item {queue_id} not found — already processed?")
            return

        if queue_item.status == QueueStatus.sent:
            logger.info(f"Queue item {queue_id} already sent — skipping")
            return

        # Mark as 'sending' so other workers don't pick it up simultaneously
        queue_item.status = QueueStatus.sending
        db.commit()

        # Load recipient details
        recipient = db.query(User).filter(User.id == recipient_id).first()
        if not recipient:
            logger.error(f"Recipient user_id={recipient_id} not found")
            _mark_failed(db, queue_item, "Recipient not found")
            return

        message = payload.get("message", "")
        subject = payload.get("subject", "School OS Notification")
        notif_type = payload.get("notification_type", "general")

        # ── Route to correct channel ─────────────────────────────────
        result = _send_via_channel(
            channel=channel,
            recipient=recipient,
            message=message,
            subject=subject,
        )

        if result["success"]:
            # ── Success path ─────────────────────────────────────────
            queue_item.status  = QueueStatus.sent
            queue_item.sent_at = datetime.utcnow()
            db.commit()

            # Write permanent record to notifications table
            _write_notification_log(
                db          = db,
                school_id   = school_id,
                recipient_id = recipient_id,
                channel     = channel,
                subject     = subject,
                content     = message,
                notif_type  = notif_type,
                status      = NotificationStatus.sent,
            )
            logger.info(
                f"Notification sent: queue_id={queue_id} "
                f"channel={channel} recipient={_recipient_label(channel, recipient)}"
            )

        else:
            # ── Failure path ─────────────────────────────────────────
            error = result.get("error", "Unknown error")
            retry_num = self.request.retries

            if retry_num >= MAX_RETRIES - 1:
                # Final attempt failed — mark permanently failed
                _mark_failed(db, queue_item, error)
                _write_notification_log(
                    db          = db,
                    school_id   = school_id,
                    recipient_id = recipient_id,
                    channel     = channel,
                    subject     = subject,
                    content     = message,
                    notif_type  = notif_type,
                    status      = NotificationStatus.failed,
                    error       = error,
                )
                logger.error(
                    f"Notification permanently failed after {MAX_RETRIES} attempts: "
                    f"queue_id={queue_id} error={error}"
                )
            else:
                # Schedule retry with exponential backoff
                countdown = RETRY_BACKOFF[retry_num]
                queue_item.status        = QueueStatus.retrying
                queue_item.retry_count   = retry_num + 1
                queue_item.next_retry_at = datetime.utcnow() + timedelta(seconds=countdown)
                queue_item.error_log     = error
                db.commit()

                logger.warning(
                    f"Notification failed (attempt {retry_num + 1}/{MAX_RETRIES}), "
                    f"retrying in {countdown}s: queue_id={queue_id} error={error}"
                )
                raise self.retry(countdown=countdown, exc=Exception(error))

    except Exception as exc:
        db.rollback()
        # Re-raise for Celery retry mechanism
        raise
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════
# QUEUE FLUSHER — runs every 2 minutes via Celery Beat
# ══════════════════════════════════════════════════════════════════════

@celery_app.task(name="flush_notification_queue")
def flush_notification_queue():
    """
    Scan notification_queue for pending items and dispatch send tasks.

    Runs every 2 minutes via Celery Beat.
    This is the bridge between agents writing to the queue
    and the send_notification task actually sending them.

    Also picks up 'retrying' items whose next_retry_at has passed.
    """
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()

        # Find all pending notifications
        pending = db.query(NotificationQueue).filter(
            NotificationQueue.status == QueueStatus.pending
        ).limit(100).all()   # process max 100 at a time

        # Find retrying notifications whose retry time has passed
        retrying = db.query(NotificationQueue).filter(
            NotificationQueue.status        == QueueStatus.retrying,
            NotificationQueue.next_retry_at <= now,
            NotificationQueue.retry_count   <  MAX_RETRIES,
        ).limit(50).all()

        all_items = pending + retrying
        dispatched = 0

        for item in all_items:
            # Dispatch individual send task
            # send_notification.delay(
            #     queue_id     = item.id,
            #     recipient_id = item.recipient_id,
            #     channel      = item.channel,
            #     payload      = item.payload,
            #     school_id    = item.school_id,
            # )
            send_notification.apply_async(
                kwargs=dict(
                    queue_id     = item.id,
                    recipient_id = item.recipient_id,
                    channel      = item.channel,
                    payload      = item.payload,
                    school_id    = item.school_id,
                ),
                queue="notifications", # <- route to dedicated worker queue
            ) 
            dispatched += 1

        if dispatched > 0:
            logger.info(
                f"[QueueFlusher] Dispatched {dispatched} notifications "
                f"({len(pending)} pending, {len(retrying)} retrying)"
            )

        return {"dispatched": dispatched}

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ══════════════════════════════════════════════════════════════════════

def _send_via_channel(
    channel:   str,
    recipient: User,
    message:   str,
    subject:   str,
) -> dict:
    """
    Route to the correct sending function based on channel name.
    Returns {"success": True/False, ...}
    """
    from app.services.notification_service import (
        send_whatsapp,
        send_sms,
        send_email,
        format_phone_for_twilio,
    )

    if channel == "whatsapp":
        if not recipient.phone:
            return {"success": False, "error": "Recipient has no phone number"}
        phone = format_phone_for_twilio(recipient.phone)
        return send_whatsapp(to_phone=phone, message=message)

    elif channel == "sms":
        if not recipient.phone:
            return {"success": False, "error": "Recipient has no phone number"}
        phone = format_phone_for_twilio(recipient.phone)
        return send_sms(to_phone=phone, message=message)

    elif channel == "email":
        if not recipient.email:
            return {"success": False, "error": "Recipient has no email"}
        return send_email(
            to_email=recipient.email,
            subject=subject,
            body=message,
        )

    elif channel == "in_app":
        # In-app: just mark as sent — the notification log write handles it
        return {"success": True, "channel": "in_app"}

    else:
        return {"success": False, "error": f"Unknown channel: {channel}"}


def _mark_failed(db: Session, queue_item: NotificationQueue, error: str) -> None:
    """Mark a queue item as permanently failed."""
    queue_item.status    = QueueStatus.failed
    queue_item.error_log = error[:500]   # truncate long errors
    db.commit()


def _write_notification_log(
    db:           Session,
    school_id:    int,
    recipient_id: int,
    channel:      str,
    subject:      str,
    content:      str,
    notif_type:   str,
    status:       NotificationStatus,
    error:        str = None,
) -> None:
    """
    Write a permanent record to the notifications table.
    This is the audit trail — notification_queue rows can be cleaned up
    but notifications table keeps everything forever.
    """
    channel_map = {
        "whatsapp": NotificationChannel.whatsapp,
        "sms":      NotificationChannel.sms,
        "email":    NotificationChannel.email,
        "in_app":   NotificationChannel.in_app,
    }
    try:
        db.add(Notification(
            school_id         = school_id,
            recipient_id      = recipient_id,
            channel           = channel_map.get(channel, NotificationChannel.in_app),
            subject           = subject,
            content           = content,
            notification_type = notif_type,
            status            = status,
            error_message     = error,
        ))
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write notification log: {e}")
        db.rollback()
