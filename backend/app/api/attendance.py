# backend/app/api/attendance.py

from fastapi import APIRouter, Depends, HTTPException, Query
import asyncio
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_school_id, TeacherOrAdmin, get_current_user
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.services.cache_service import cache_invalidate, make_cache_key

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

class AttendanceMarkRequest(BaseModel):
    student_id: int
    class_id: int
    date: date
    status: AttendanceStatus
    notes: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    class_id: int
    date: date
    status: AttendanceStatus
    notes: Optional[str]
    class Config:
        from_attributes = True


@router.post("", response_model=AttendanceResponse, status_code=201)
async def mark_attendance(
    payload: AttendanceMarkRequest,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    current_user: User = Depends(get_current_user),
    _=TeacherOrAdmin
):
    """
    Mark attendance for a student.
    After saving, publishes a Redis event so the Attendance Agent
    can immediately check for absence patterns.
    """
    # Check if attendance already marked for this student on this date
    existing = db.query(Attendance).filter(
        Attendance.student_id == payload.student_id,
        Attendance.date == payload.date,
        Attendance.school_id == school_id
    ).first()

    if existing:
        # Update existing record instead of creating duplicate
        existing.status = payload.status
        existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        record = existing
    else:
        record = Attendance(
            school_id=school_id,
            marked_by=current_user.id,
            **payload.model_dump()
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    # Invalidate attendance cache
    await cache_invalidate(f"attendance:{school_id}:*")

    # # Publish event for Attendance Agent (Phase 4)
    # # We import lazily so Phase 3 works even before Phase 4 is built
    # try:
    #     from app.events.publisher import publish_event
    #     import asyncio
    #     asyncio.create_task(publish_event("attendance.marked", {
    #         "school_id":  school_id,
    #         "student_id": payload.student_id,
    #         "date":       str(payload.date),
    #         "status":     payload.status.value,
    #     }))
    # except Exception:
    #     pass  # event publishing is best-effort — don't fail the API call

    # return record
    # backend/app/api/attendance.py
# Replace the try/except event block in mark_attendance() with this:

    from app.events.publisher import publish_event, Events

    asyncio.create_task(
        publish_event(Events.ATTENDANCE_MARKED, {
            "school_id":  school_id,
            "student_id": payload.student_id,
            "class_id":   payload.class_id,
            "date":       str(payload.date),
            "status":     payload.status.value,
            "marked_by":  current_user.id,
        })
    )

    return record


@router.get("", response_model=List[AttendanceResponse])
async def get_attendance(
    student_id: Optional[int] = Query(None),
    class_id:   Optional[int] = Query(None),
    from_date:  Optional[date] = Query(None),
    to_date:    Optional[date] = Query(None),
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
):
    """Get attendance records with optional filters."""
    q = db.query(Attendance).filter(Attendance.school_id == school_id)
    if student_id: q = q.filter(Attendance.student_id == student_id)
    if class_id:   q = q.filter(Attendance.class_id   == class_id)
    if from_date:  q = q.filter(Attendance.date >= from_date)
    if to_date:    q = q.filter(Attendance.date <= to_date)
    return q.order_by(Attendance.date.desc()).limit(500).all()