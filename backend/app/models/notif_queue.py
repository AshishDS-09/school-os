# backend/app/models/notif_queue.py

from sqlalchemy import Column, Integer, ForeignKey, String, Enum, JSON, DateTime
import enum
from datetime import datetime
from app.models.base import Base, TimestampMixin

class QueueStatus(str, enum.Enum):
    pending  = "pending"   # waiting to be picked up by worker
    sending  = "sending"   # currently being processed
    sent     = "sent"      # successfully delivered
    retrying = "retrying"  # failed once, will retry
    failed   = "failed"    # failed 3 times — give up

class NotificationQueue(Base, TimestampMixin):
    __tablename__ = "notification_queue"

    school_id    = Column(Integer, ForeignKey("schools.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"),   nullable=False)

    channel      = Column(String(20),  nullable=False)  # "whatsapp", "email", "sms"
    # payload: full message data as JSON
    # e.g. {"message": "Fee due...", "template": "fee_reminder", "data": {...}}
    payload      = Column(JSON,        nullable=False)
    status       = Column(Enum(QueueStatus), default=QueueStatus.pending)
    # retry_count: incremented each time sending fails
    retry_count  = Column(Integer,     default=0)
    # next_retry_at: when to attempt sending again
    next_retry_at = Column(DateTime,   nullable=True)
    sent_at      = Column(DateTime,    nullable=True)
    error_log    = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<Queue {self.channel} status={self.status} retries={self.retry_count}>"