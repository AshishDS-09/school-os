# backend/app/services/notification_service.py

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── WhatsApp via Twilio ───────────────────────────────────────────────

def send_whatsapp(to_phone: str, message: str) -> dict:
    """
    Send a WhatsApp message via Twilio sandbox.

    Args:
        to_phone:  Recipient phone number.
                   Must include country code: "+919876543210"
                   Do NOT include 'whatsapp:' prefix here — we add it.
        message:   Plain text message body (max 1600 chars for WhatsApp)

    Returns:
        {"success": True, "sid": "SM..."} on success
        {"success": False, "error": "..."} on failure

    Important for Indian numbers:
        Always use +91 prefix: "+919876543210"
        Twilio sandbox works with any WhatsApp-enabled number.
    """
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Ensure phone has whatsapp: prefix for recipient
        to_whatsapp = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone

        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_whatsapp,
            body=message,
        )

        logger.info(f"WhatsApp sent: sid={msg.sid} to={to_phone}")
        return {"success": True, "sid": msg.sid, "status": msg.status}

    except Exception as e:
        logger.error(f"WhatsApp send failed to {to_phone}: {e}")
        return {"success": False, "error": str(e)}


# ── SMS via Twilio ────────────────────────────────────────────────────

def send_sms(to_phone: str, message: str) -> dict:
    """
    Send an SMS via Twilio.
    Use this as fallback when parent doesn't have WhatsApp.
    Requires a Twilio phone number (not the WhatsApp sandbox number).
    """
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        msg = client.messages.create(
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone,
            body=message,
        )

        logger.info(f"SMS sent: sid={msg.sid} to={to_phone}")
        return {"success": True, "sid": msg.sid}

    except Exception as e:
        logger.error(f"SMS send failed to {to_phone}: {e}")
        return {"success": False, "error": str(e)}


# ── Email via SendGrid ────────────────────────────────────────────────

def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> dict:
    """
    Send a transactional email via SendGrid.

    Args:
        to_email:   Recipient email address
        subject:    Email subject line
        body:       Plain text body (always include this)
        html_body:  Optional HTML version (richer formatting)
    """
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Content, MimeType

        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        mail = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=to_email,
        )
        mail.subject = subject

        # Always attach plain text
        mail.add_content(Content(MimeType.text, body))

        # Attach HTML version if provided
        if html_body:
            mail.add_content(Content(MimeType.html, html_body))

        response = sg.send(mail)

        success = response.status_code in (200, 201, 202)
        logger.info(
            f"Email {'sent' if success else 'failed'}: "
            f"to={to_email} status={response.status_code}"
        )
        return {"success": success, "status_code": response.status_code}

    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")
        return {"success": False, "error": str(e)}


# ── In-app notification (stored in DB only) ───────────────────────────

def send_in_app(recipient_id: int, message: str, notification_type: str) -> dict:
    """
    Store an in-app notification in the notifications table.
    The frontend reads this via GET /api/notifications.
    No external API call needed — just a DB write.
    """
    from app.core.database import SessionLocal
    from app.models.notification import Notification, NotificationChannel, NotificationStatus

    db = SessionLocal()
    try:
        db.add(Notification(
            school_id=0,           # filled by caller if needed
            recipient_id=recipient_id,
            channel=NotificationChannel.in_app,
            content=message,
            notification_type=notification_type,
            status=NotificationStatus.sent,
        ))
        db.commit()
        return {"success": True, "channel": "in_app"}
    except Exception as e:
        logger.error(f"In-app notification failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# ── Phone number formatter ────────────────────────────────────────────

def format_phone_for_twilio(phone: str) -> str:
    """
    Ensure phone number is in E.164 format for Twilio.
    Indian numbers: 9876543210 → +919876543210
    Already formatted: +919876543210 → +919876543210

    Twilio requires E.164: +[country_code][number]
    """
    phone = phone.strip().replace(" ", "").replace("-", "")

    if phone.startswith("+"):
        return phone   # already E.164

    # Indian 10-digit number
    if len(phone) == 10 and phone.isdigit():
        return f"+91{phone}"

    # Indian number with 91 prefix
    if phone.startswith("91") and len(phone) == 12:
        return f"+{phone}"

    # Return as-is for other formats
    return f"+{phone}" if not phone.startswith("+") else phone