# backend/app/models/school.py

from sqlalchemy import Column, String, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin

class SubscriptionTier(str, enum.Enum):
    basic = "basic"       # ₹999/month — basic features only
    smart = "smart"       # ₹1999/month — + AI risk detection
    pro   = "pro"         # ₹3499/month — all 10 agents

class School(Base, TimestampMixin):
    __tablename__ = "schools"

    name              = Column(String(200), nullable=False)
    email             = Column(String(200), unique=True, nullable=False)
    phone             = Column(String(20))
    address           = Column(String(500))
    city              = Column(String(100))
    state             = Column(String(100))
    subscription_tier = Column(
        Enum(SubscriptionTier),
        default=SubscriptionTier.basic,
        nullable=False
    )
    is_active         = Column(Boolean, default=True)
    # Stores flexible settings like: language preference, timezone, logo URL
    settings_json     = Column(JSON, default={})

    # Relationships — SQLAlchemy uses these for joins
    users    = relationship("User",    back_populates="school")
    students = relationship("Student", back_populates="school")

    def __repr__(self):
        return f"<School {self.name}>"