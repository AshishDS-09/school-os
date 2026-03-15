# backend/app/models/fee.py

from sqlalchemy import Column, Integer, ForeignKey, String, Float, Date, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin

class FeeStatus(str, enum.Enum):
    pending    = "pending"    # not yet due
    due        = "due"        # due date reached, not paid
    overdue    = "overdue"    # past due date, not paid
    paid       = "paid"       # fully paid
    partial    = "partial"    # partially paid
    waived     = "waived"     # fee waived by admin

class FeeType(str, enum.Enum):
    tuition    = "tuition"
    transport  = "transport"
    exam       = "exam"
    sports     = "sports"
    library    = "library"
    other      = "other"

class FeeRecord(Base, TimestampMixin):
    __tablename__ = "fee_records"

    school_id    = Column(Integer, ForeignKey("schools.id"),  nullable=False)
    student_id   = Column(Integer, ForeignKey("students.id"), nullable=False)

    fee_type     = Column(Enum(FeeType),   nullable=False)
    amount       = Column(Float,           nullable=False)  # total amount due
    amount_paid  = Column(Float,           default=0.0)     # how much paid so far
    due_date     = Column(Date,            nullable=False)
    paid_date    = Column(Date,            nullable=True)   # null if not paid yet
    status       = Column(Enum(FeeStatus), default=FeeStatus.pending)
    academic_year = Column(String(20),     nullable=False)  # "2024-25"
    description  = Column(String(300),     nullable=True)
    # receipt_number: generated when payment received
    receipt_number = Column(String(50),    nullable=True)
    # reminder_count: how many reminders sent — agent uses this
    reminder_count = Column(Integer,       default=0)

    student = relationship("Student", back_populates="fee_records")

    @property
    def balance_due(self):
        return round(self.amount - self.amount_paid, 2)

    def __repr__(self):
        return f"<Fee student={self.student_id} amount={self.amount} status={self.status}>"