# backend/app/api/marks.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
import asyncio
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_school_id, TeacherOrAdmin, get_current_user
from app.models.marks import Marks, ExamType
from app.models.user import User
from app.services.cache_service import cache_invalidate

router = APIRouter(prefix="/api/marks", tags=["Marks"])

class MarksCreateRequest(BaseModel):
    student_id: int
    class_id:   int
    subject:    str
    exam_type:  ExamType
    exam_date:  date
    score:      float
    max_score:  float
    remarks:    Optional[str] = None

class MarksResponse(BaseModel):
    id: int
    student_id: int
    subject: str
    exam_type: ExamType
    exam_date: date
    score: float
    max_score: float
    percentage: float
    remarks: Optional[str]
    class Config:
        from_attributes = True


@router.post("", response_model=MarksResponse, status_code=201)
async def enter_marks(
    payload: MarksCreateRequest,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    current_user: User = Depends(get_current_user),
    _=TeacherOrAdmin
):
    """
    Enter exam marks for a student.
    Publishes marks.entered event → triggers Academic Agent immediately.
    """
    record = Marks(
        school_id=school_id,
        entered_by=current_user.id,
        **payload.model_dump()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Invalidate marks cache for this student
    await cache_invalidate(f"marks:{school_id}:{payload.student_id}:*")

    # Publish event → Academic Agent runs immediately (Phase 4+)
    # try:
    #     from app.events.publisher import publish_event
    #     import asyncio
    #     asyncio.create_task(publish_event("marks.entered", {
    #         "school_id":  school_id,
    #         "student_id": payload.student_id,
    #         "subject":    payload.subject,
    #         "score":      payload.score,
    #         "max_score":  payload.max_score,
    #         "percentage": record.percentage,
    #     }))
    # except Exception:
    #     pass

    # return record
    # backend/app/api/marks.py
    # Replace the try/except event block at the bottom of enter_marks() with this:

    # ── Publish event AFTER successful DB write ──────────────────
    # Import here so Phase 3 still works if subscriber isn't running yet
    from app.events.publisher import publish_event, Events

    # asyncio.create_task runs publish_event in the background
    # The API response returns immediately — no waiting for Redis
    asyncio.create_task(
        publish_event(Events.MARKS_ENTERED, {
            "school_id":  school_id,
            "student_id": payload.student_id,
            "class_id":   payload.class_id,
            "subject":    payload.subject,
            "exam_type":  payload.exam_type.value,
            "score":      payload.score,
            "max_score":  payload.max_score,
            "percentage": record.percentage,
            "entered_by": current_user.id,
        })
    )

    return record


@router.get("", response_model=List[MarksResponse])
async def get_marks(
    student_id: Optional[int] = Query(None),
    subject:    Optional[str] = Query(None),
    db: Session = Depends(get_db),
    school_id:  int = Depends(get_current_school_id),
):
    q = db.query(Marks).filter(Marks.school_id == school_id)
    if student_id: q = q.filter(Marks.student_id == student_id)
    if subject:    q = q.filter(Marks.subject    == subject)
    return q.order_by(Marks.exam_date.desc()).limit(200).all()