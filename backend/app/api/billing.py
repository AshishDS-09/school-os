# backend/app/api/billing.py

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_school_id
from app.core.subscription import get_tier_info, TIER_FEATURES
from app.models.school import School, SubscriptionTier
from app.models.user import User
from app.services.razorpay_service import (
    create_order, verify_payment_signature,
    verify_webhook_signature, RAZORPAY_PLANS,
)
from app.core.config import settings

router = APIRouter(prefix="/api/billing", tags=["Billing"])
logger = logging.getLogger(__name__)


# ── Request/Response schemas ──────────────────────────────────────

class CreateOrderRequest(BaseModel):
    tier: str   # "basic" | "smart" | "pro"

class VerifyPaymentRequest(BaseModel):
    order_id:   str
    payment_id: str
    signature:  str
    tier:       str


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/plans")
def get_plans():
    """
    Public endpoint — returns all plan details for pricing page.
    No auth required so visitors can see pricing before signing up.
    """
    return {
        "plans": [
            {
                "tier":        tier,
                "label":       plan["label"],
                "amount":      plan["amount"] // 100,  # convert paise → rupees
                "currency":    "INR",
                "description": plan["description"],
                "features":    TIER_FEATURES.get(
                    SubscriptionTier(tier),
                    {}
                ),
            }
            for tier, plan in RAZORPAY_PLANS.items()
        ]
    }


@router.get("/status")
def get_billing_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Current school's subscription info — shown in billing dashboard."""
    info = get_tier_info(current_user.school_id, db)

    school = db.query(School).filter(
        School.id == current_user.school_id
    ).first()

    return {
        **info,
        "school_name": school.name if school else "",
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }


@router.post("/create-order")
def create_payment_order(
    payload: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Step 1 of payment flow:
        Frontend calls this → gets order_id
        Frontend opens Razorpay modal with order_id
        User pays → Razorpay calls /verify-payment
    """
    if payload.tier not in ("basic", "smart", "pro"):
        raise HTTPException(
            status_code=400,
            detail="Invalid tier. Must be: basic, smart, or pro"
        )

    try:
        order = create_order(
            tier=payload.tier,
            school_id=current_user.school_id,
        )
        return {
            "order_id":   order["id"],
            "amount":     order["amount"],
            "currency":   order["currency"],
            "tier":       payload.tier,
            "key_id":     settings.RAZORPAY_KEY_ID,
        }
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Payment order creation failed. Please try again."
        )


@router.post("/verify-payment")
def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Step 2 of payment flow:
        Called by frontend AFTER Razorpay modal closes with success.
        Verifies the signature is genuine (prevents fraud).
        Activates the new subscription tier.
    """
    # Verify signature — this is the anti-fraud check
    is_valid = verify_payment_signature(
        order_id   = payload.order_id,
        payment_id = payload.payment_id,
        signature  = payload.signature,
    )

    if not is_valid:
        logger.warning(
            f"FRAUD ATTEMPT: Invalid payment signature "
            f"school_id={current_user.school_id} "
            f"payment_id={payload.payment_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed. Contact support if you were charged."
        )

    # Map tier string to enum
    tier_map = {
        "basic": SubscriptionTier.basic,
        "smart": SubscriptionTier.smart,
        "pro":   SubscriptionTier.pro,
    }
    new_tier = tier_map.get(payload.tier)
    if not new_tier:
        raise HTTPException(status_code=400, detail="Invalid tier")

    # Activate the subscription
    school = db.query(School).filter(
        School.id == current_user.school_id
    ).first()

    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    old_tier = school.subscription_tier
    school.subscription_tier = new_tier
    db.commit()

    logger.info(
        f"Subscription upgraded: school_id={school.id} "
        f"{old_tier.value} → {new_tier.value} "
        f"payment_id={payload.payment_id}"
    )

    return {
        "success":   True,
        "message":   f"Plan upgraded to {payload.tier.title()} successfully!",
        "old_tier":  old_tier.value,
        "new_tier":  new_tier.value,
        "payment_id": payload.payment_id,
    }


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Razorpay sends events here automatically:
        - subscription.activated
        - subscription.charged    (monthly renewal)
        - subscription.cancelled
        - payment.failed

    Configure webhook URL in Razorpay Dashboard →
    Settings → Webhooks → Add new webhook
    URL: https://yourapi.com/api/billing/webhook
    """
    body      = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify the webhook is genuinely from Razorpay
    if not verify_webhook_signature(body, signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("event")
    payload    = event.get("payload", {})
    logger.info(f"Razorpay webhook received: {event_type}")

    # ── Handle subscription events ───────────────────────────────
    if event_type == "subscription.activated":
        sub  = payload.get("subscription", {}).get("entity", {})
        notes = sub.get("notes", {})
        school_id = notes.get("school_id")
        tier      = notes.get("tier")

        if school_id and tier:
            school = db.query(School).filter(
                School.id == int(school_id)
            ).first()
            if school:
                tier_map = {
                    "basic": SubscriptionTier.basic,
                    "smart": SubscriptionTier.smart,
                    "pro":   SubscriptionTier.pro,
                }
                school.subscription_tier = tier_map.get(tier, SubscriptionTier.basic)
                db.commit()
                logger.info(f"Subscription activated: school_id={school_id} tier={tier}")

    elif event_type == "subscription.cancelled":
        sub   = payload.get("subscription", {}).get("entity", {})
        notes = sub.get("notes", {})
        school_id = notes.get("school_id")

        if school_id:
            school = db.query(School).filter(
                School.id == int(school_id)
            ).first()
            if school:
                # Downgrade to basic on cancellation
                school.subscription_tier = SubscriptionTier.basic
                db.commit()
                logger.info(f"Subscription cancelled: school_id={school_id} → downgraded to basic")

    elif event_type == "payment.failed":
        logger.warning(f"Payment failed: {payload}")
        # In production: notify admin, send retry link to school

    return {"status": "ok", "event": event_type}


@router.post("/downgrade")
def downgrade_to_basic(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually downgrade a school to basic tier (admin action)."""
    school = db.query(School).filter(
        School.id == current_user.school_id
    ).first()
    if school:
        school.subscription_tier = SubscriptionTier.basic
        db.commit()
    return {"success": True, "tier": "basic"}