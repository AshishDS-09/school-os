# backend/app/core/subscription.py

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.school import School, SubscriptionTier
from app.models.user import User


# ── What each tier can access ─────────────────────────────────────

TIER_FEATURES = {
    SubscriptionTier.basic: {
        "max_students":        200,
        "max_teachers":        20,
        "attendance":          True,
        "fees":                True,
        "marks":               True,
        "notifications":       True,
        # AI features — all False for basic
        "academic_agent":      False,
        "attendance_agent":    False,
        "fee_agent":           False,
        "teacher_copilot":     False,
        "admission_agent":     False,
        "behavioral_agent":    False,
        "learning_agent":      False,
        "teacher_performance": False,
        "admin_workflow":      False,
        "parent_comm":         False,
    },
    SubscriptionTier.smart: {
        "max_students":        500,
        "max_teachers":        50,
        "attendance":          True,
        "fees":                True,
        "marks":               True,
        "notifications":       True,
        # Core AI agents — True for smart
        "academic_agent":      True,
        "attendance_agent":    True,
        "fee_agent":           True,
        "teacher_copilot":     False,
        "admission_agent":     True,
        "behavioral_agent":    False,
        "learning_agent":      False,
        "teacher_performance": False,
        "admin_workflow":      False,
        "parent_comm":         True,
    },
    SubscriptionTier.pro: {
        "max_students":        5000,
        "max_teachers":        500,
        "attendance":          True,
        "fees":                True,
        "marks":               True,
        "notifications":       True,
        # All 10 agents — True for pro
        "academic_agent":      True,
        "attendance_agent":    True,
        "fee_agent":           True,
        "teacher_copilot":     True,
        "admission_agent":     True,
        "behavioral_agent":    True,
        "learning_agent":      True,
        "teacher_performance": True,
        "admin_workflow":      True,
        "parent_comm":         True,
    },
}


def get_school_tier(school_id: int, db: Session) -> SubscriptionTier:
    """Fetch the current subscription tier for a school."""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return SubscriptionTier.basic
    return school.subscription_tier


def check_feature(feature: str):
    """
    FastAPI dependency factory — blocks access if school's tier
    doesn't include the requested feature.

    Usage:
        @router.post("/ai/lesson-plan")
        def generate(
            _=Depends(check_feature("teacher_copilot")),
        ):
    """
    def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        tier     = get_school_tier(current_user.school_id, db)
        features = TIER_FEATURES.get(tier, TIER_FEATURES[SubscriptionTier.basic])

        if not features.get(feature, False):
            tier_names = {
                SubscriptionTier.basic: "Basic (₹999/month)",
                SubscriptionTier.smart: "Smart (₹1999/month)",
                SubscriptionTier.pro:   "Pro (₹3499/month)",
            }
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error":           "feature_not_available",
                    "feature":         feature,
                    "current_tier":    tier.value,
                    "upgrade_message": (
                        f"'{feature}' is not available on your current "
                        f"{tier_names[tier]} plan. Upgrade to unlock this feature."
                    ),
                    "upgrade_url":     "/billing/upgrade",
                }
            )
        return current_user

    return Depends(_check)


def get_tier_info(school_id: int, db: Session) -> dict:
    """
    Returns full tier info for the billing dashboard.
    """
    tier     = get_school_tier(school_id, db)
    features = TIER_FEATURES.get(tier, {})

    pricing  = {
        SubscriptionTier.basic: {"price": 999,  "label": "Basic"},
        SubscriptionTier.smart: {"price": 1999, "label": "Smart"},
        SubscriptionTier.pro:   {"price": 3499, "label": "Pro"},
    }

    return {
        "current_tier":   tier.value,
        "price_per_month": pricing[tier]["price"],
        "label":          pricing[tier]["label"],
        "features":       features,
        "all_tiers":      {
            t.value: {
                **TIER_FEATURES[t],
                "price": pricing[t]["price"],
                "label": pricing[t]["label"],
            }
            for t in SubscriptionTier
        },
    }