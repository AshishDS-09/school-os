# backend/app/api/leads.py

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_school_id, AnyUser, TeacherOrAdmin
from app.models.lead import Lead, LeadStatus
from app.events.publisher import publish_event, Events

router = APIRouter(prefix="/api/leads", tags=["Leads"])

class LeadCreateRequest(BaseModel):
    parent_name:        str
    parent_phone:       str
    parent_email:       Optional[str] = None
    child_name:         str
    applying_for_grade: str
    academic_year:      str
    source:             Optional[str] = "website"
    notes:              Optional[str] = None

class LeadResponse(BaseModel):
    id:                 int
    parent_name:        str
    parent_phone:       str
    child_name:         str
    applying_for_grade: str
    status:             LeadStatus
    source:             Optional[str]
    follow_up_count:    int
    created_at:         datetime
    class Config:
        from_attributes = True


class LeadUpdateRequest(BaseModel):
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(
    payload: LeadCreateRequest,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
):
    """
    Create a new admission lead (parent enquiry).
    Publishes lead.created → Admission Agent qualifies and follows up.
    This endpoint is also called from the school's public website form.
    """
    lead = Lead(school_id=school_id, **payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)

    asyncio.create_task(
        publish_event(Events.LEAD_CREATED, {
            "school_id":  school_id,
            "lead_id":    lead.id,
            "parent_name":  payload.parent_name,
            "parent_phone": payload.parent_phone,
            "child_name":   payload.child_name,
            "grade":        payload.applying_for_grade,
        })
    )

    return lead


@router.get("", response_model=List[LeadResponse])
def list_leads(
    status: Optional[LeadStatus] = None,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=AnyUser
):
    q = db.query(Lead).filter(Lead.school_id == school_id)
    if status:
        q = q.filter(Lead.status == status)
    return q.order_by(Lead.created_at.desc()).all()


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    payload: LeadUpdateRequest,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin,
):
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.school_id == school_id,
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead
