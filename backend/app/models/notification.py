# backend/app/models/notification.py

from sqlalchemy import Column, Integer, ForeignKey, String, Enum, Text, Boolean
import enum
from app.models.base import Base, TimestampMixin

class NotificationChannel(str, enum.Enum):
    whatsapp = "whatsapp"
    sms      = "sms"
    email    = "email"
    in_app   = "in_app"

class NotificationStatus(str, enum.Enum):
    sent    = "sent"
    failed  = "failed"
    pending = "pending"

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    school_id    = Column(Integer, ForeignKey("schools.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"),   nullable=False)

    channel      = Column(Enum(NotificationChannel), nullable=False)
    subject      = Column(String(300),  nullable=True)   # for email
    content      = Column(Text,         nullable=False)  # full message text
    status       = Column(Enum(NotificationStatus), default=NotificationStatus.pending)
    # notification_type: "fee_reminder", "attendance_alert", "academic_risk" etc.
    notification_type = Column(String(100), nullable=False)
    # triggered_by: which agent sent this — "fee_agent", "academic_agent"
    triggered_by = Column(String(100),  nullable=True)
    error_message = Column(Text,        nullable=True)   # if failed, why

    def __repr__(self):
        return f"<Notification {self.notification_type} via {self.channel} → {self.recipient_id}>"