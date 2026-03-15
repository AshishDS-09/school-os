# backend/app/api/notifications.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_school_id
from app.models.notification import Notification, NotificationChannel, NotificationStatus

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

class NotificationResponse(BaseModel):
    id: int
    recipient_id: int
    channel: NotificationChannel
    subject: Optional[str]
    content: str
    status: NotificationStatus
    notification_type: str
    triggered_by: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    recipient_id: Optional[int]    = Query(None),
    channel:      Optional[str]    = Query(None),
    db: Session = Depends(get_db),
    school_id:    int = Depends(get_current_school_id),
):
    """List all notifications sent by agents for this school."""
    q = db.query(Notification).filter(Notification.school_id == school_id)
    if recipient_id: q = q.filter(Notification.recipient_id == recipient_id)
    if channel:      q = q.filter(Notification.channel      == channel)
    return q.order_by(Notification.created_at.desc()).limit(100).all()