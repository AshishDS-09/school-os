# backend/app/api/fees.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_school_id, TeacherOrAdmin
from app.models.fee import FeeRecord, FeeStatus, FeeType
from app.services.cache_service import cache_get, cache_set, cache_invalidate, CACHE_TTL

router = APIRouter(prefix="/api/fees", tags=["Fees"])

class FeeCreateRequest(BaseModel):
    student_id:    int
    fee_type:      FeeType
    amount:        float
    due_date:      date
    academic_year: str
    description:   Optional[str] = None

class FeeUpdateRequest(BaseModel):
    amount_paid:    Optional[float] = None
    status:         Optional[FeeStatus] = None
    paid_date:      Optional[date] = None
    receipt_number: Optional[str] = None

class FeeResponse(BaseModel):
    id: int
    student_id: int
    fee_type: FeeType
    amount: float
    amount_paid: float
    balance_due: float
    due_date: date
    paid_date: Optional[date]
    status: FeeStatus
    academic_year: str
    reminder_count: int
    class Config:
        from_attributes = True


@router.get("", response_model=List[FeeResponse])
async def list_fees(
    student_id: Optional[int]      = Query(None),
    status:     Optional[FeeStatus] = Query(None),
    db: Session = Depends(get_db),
    school_id:  int = Depends(get_current_school_id),
):
    """List fee records. Filter by student or status (overdue, paid etc.)"""
    q = db.query(FeeRecord).filter(FeeRecord.school_id == school_id)
    if student_id: q = q.filter(FeeRecord.student_id == student_id)
    if status:     q = q.filter(FeeRecord.status     == status)
    return q.order_by(FeeRecord.due_date.desc()).all()


@router.post("", response_model=FeeResponse, status_code=201)
async def create_fee(
    payload: FeeCreateRequest,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin
):
    record = FeeRecord(school_id=school_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    await cache_invalidate(f"fees:{school_id}:*")
    return record


@router.patch("/{fee_id}", response_model=FeeResponse)
async def update_fee(
    fee_id: int,
    payload: FeeUpdateRequest,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin
):
    """Record a payment or update fee status."""
    fee = db.query(FeeRecord).filter(
        FeeRecord.id == fee_id,
        FeeRecord.school_id == school_id
    ).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(fee, field, value)

    # Auto-set status to paid if fully paid
    if fee.amount_paid >= fee.amount:
        fee.status = FeeStatus.paid

    db.commit()
    db.refresh(fee)
    await cache_invalidate(f"fees:{school_id}:*")
    return fee