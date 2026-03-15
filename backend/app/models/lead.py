# backend/app/models/lead.py

from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, Enum, Boolean, DateTime
import enum
from app.models.base import Base, TimestampMixin

class LeadStatus(str, enum.Enum):
    new          = "new"           # just submitted inquiry
    contacted    = "contacted"     # admission team reached out
    visit_scheduled = "visit_scheduled"  # school visit booked
    visited      = "visited"       # came to school
    applied      = "applied"       # submitted application
    admitted     = "admitted"      # confirmed admission
    rejected     = "rejected"      # did not convert
    lost         = "lost"          # went to another school

class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    school_id    = Column(Integer, ForeignKey("schools.id"), nullable=False)
    # assigned_to: admission staff user_id handling this lead
    assigned_to  = Column(Integer, ForeignKey("users.id"),   nullable=True)

    # Parent / guardian info
    parent_name  = Column(String(200), nullable=False)
    parent_email = Column(String(200), nullable=True)
    parent_phone = Column(String(20),  nullable=False)

    # Child info
    child_name   = Column(String(200), nullable=False)
    # applying_for_grade: "5", "6", "7" etc.
    applying_for_grade = Column(String(20), nullable=False)
    academic_year = Column(String(20),  nullable=False)

    status       = Column(Enum(LeadStatus), default=LeadStatus.new)
    source       = Column(String(100),  nullable=True)  # "website", "referral", "walk-in"
    notes        = Column(Text,         nullable=True)
    # visit_scheduled_at: datetime of booked school tour
    visit_scheduled_at = Column(DateTime, nullable=True)
    # follow_up_count: how many times admission agent followed up
    follow_up_count = Column(Integer, default=0)
    # last_follow_up: date of last AI follow-up message
    last_follow_up = Column(Date, nullable=True)

    def __repr__(self):
        return f"<Lead {self.parent_name} → {self.child_name} status={self.status}>"