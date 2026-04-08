# backend/app/api/attendance.py

from fastapi import APIRouter, Depends, HTTPException, Query
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.core.security import get_current_school_id, TeacherOrAdmin, get_current_user
from app.models.attendance import Attendance, AttendanceStatus
from app.models.class_ import Class_
from app.models.student import Student
from app.models.user import User
from app.services.cache_service import cache_invalidate

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
logger = logging.getLogger(__name__)

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
    class_ = db.query(Class_).filter(
        Class_.id == payload.class_id,
        Class_.school_id == school_id
    ).first()
    if not class_:
        raise HTTPException(status_code=400, detail="Selected class was not found in your school.")

    student = db.query(Student).filter(
        Student.id == payload.student_id,
        Student.school_id == school_id
    ).first()
    if not student:
        raise HTTPException(status_code=400, detail="Selected student was not found in your school.")
    if student.class_id != payload.class_id:
        raise HTTPException(status_code=400, detail="Student does not belong to the selected class.")

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
        try:
            db.commit()
            db.refresh(existing)
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not save attendance due to invalid linked records.")
        record = existing
    else:
        record = Attendance(
            school_id=school_id,
            marked_by=current_user.id,
            **payload.model_dump()
        )
        try:
            db.add(record)
            db.commit()
            db.refresh(record)
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Could not save attendance due to invalid linked records.")

    # Invalidate attendance cache
    try:
        await cache_invalidate(f"attendance:{school_id}:*")
    except Exception as exc:
        logger.warning("Attendance cache invalidate failed for school_id=%s: %s", school_id, exc)

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

    try:
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
    except Exception as exc:
        logger.warning("Attendance event publish failed for student_id=%s school_id=%s: %s", payload.student_id, school_id, exc)

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
