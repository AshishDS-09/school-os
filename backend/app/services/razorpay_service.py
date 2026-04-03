# backend/app/services/razorpay_service.py

import hmac
import hashlib
import logging
from typing import Optional

import razorpay

from app.core.config import settings

logger = logging.getLogger(__name__)

# Razorpay plan IDs — create these in Razorpay dashboard
# Dashboard → Products → Subscriptions → Plans → Create Plan
# We store the plan IDs here after creating them
RAZORPAY_PLANS = {
    "basic": {
        "plan_id":    "plan_basic_xxxx",   # replace after creating in dashboard
        "amount":     99900,               # ₹999 in paise (1 rupee = 100 paise)
        "currency":   "INR",
        "period":     "monthly",
        "interval":   1,
        "label":      "Basic",
        "description": "Basic school management — up to 200 students",
    },
    "smart": {
        "plan_id":    "plan_smart_xxxx",   # replace after creating
        "amount":     199900,
        "currency":   "INR",
        "period":     "monthly",
        "interval":   1,
        "label":      "Smart",
        "description": "AI risk detection + parent communication",
    },
    "pro": {
        "plan_id":    "plan_pro_xxxx",     # replace after creating
        "amount":     349900,
        "currency":   "INR",
        "period":     "monthly",
        "interval":   1,
        "label":      "Pro",
        "description": "All 10 AI agents — unlimited potential",
    },
}


def get_razorpay_client() -> razorpay.Client:
    """Returns authenticated Razorpay client."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_subscription(tier: str, school_id: int) -> dict:
    """
    Create a Razorpay subscription for a school.

    Returns the subscription object with:
        - id:          subscription_id to send to frontend
        - short_url:   payment link (optional)
        - status:      "created"

    The frontend uses subscription_id with Razorpay.js to open
    the payment modal.
    """
    client  = get_razorpay_client()
    plan    = RAZORPAY_PLANS.get(tier)

    if not plan:
        raise ValueError(f"Unknown tier: {tier}")

    subscription = client.subscription.create({
        "plan_id":          plan["plan_id"],
        "total_count":      12,         # 12 months
        "quantity":         1,
        "notes": {
            "school_id":    str(school_id),
            "tier":         tier,
        },
    })

    logger.info(
        f"Razorpay subscription created: "
        f"school_id={school_id} tier={tier} "
        f"sub_id={subscription['id']}"
    )

    return subscription


def create_order(tier: str, school_id: int) -> dict:
    """
    Create a one-time Razorpay order for the first month payment.
    Used to verify payment before activating subscription.
    """
    client = get_razorpay_client()
    plan   = RAZORPAY_PLANS.get(tier)

    if not plan:
        raise ValueError(f"Unknown tier: {tier}")

    order = client.order.create({
        "amount":   plan["amount"],
        "currency": plan["currency"],
        "notes": {
            "school_id": str(school_id),
            "tier":      tier,
        },
    })

    logger.info(
        f"Razorpay order created: school_id={school_id} "
        f"tier={tier} order_id={order['id']}"
    )

    return order


def verify_payment_signature(
    order_id:    str,
    payment_id:  str,
    signature:   str,
) -> bool:
    """
    Verify that a payment_id + signature received from the frontend
    is genuinely from Razorpay and not forged.

    This MUST be called before activating any subscription.
    """
    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id":   order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature":  signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        logger.warning(
            f"Payment signature verification FAILED: "
            f"order_id={order_id} payment_id={payment_id}"
        )
        return False


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify that a webhook event came from Razorpay.
    Called in the webhook handler before processing any event.
    """
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def get_subscription_status(subscription_id: str) -> dict:
    """Fetch current status of a Razorpay subscription."""
    client = get_razorpay_client()
    return client.subscription.fetch(subscription_id)