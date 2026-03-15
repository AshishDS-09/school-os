# backend/app/api/incidents.py

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_school_id, TeacherOrAdmin, get_current_user
from app.models.incident import Incident, IncidentType, IncidentSeverity
from app.models.user import User
from app.events.publisher import publish_event, Events

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

class IncidentCreateRequest(BaseModel):
    student_id:    int
    incident_type: IncidentType
    severity:      IncidentSeverity
    incident_date: date
    description:   str
    action_taken:  Optional[str] = None

class IncidentResponse(BaseModel):
    id:            int
    student_id:    int
    incident_type: IncidentType
    severity:      IncidentSeverity
    incident_date: date
    description:   str
    action_taken:  Optional[str]
    is_resolved:   bool
    class Config:
        from_attributes = True


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreateRequest,
    db: Session = Depends(get_db),
    school_id:    int  = Depends(get_current_school_id),
    current_user: User = Depends(get_current_user),
    _=TeacherOrAdmin
):
    """
    Log a behavioral incident for a student.
    Publishes incident.created → triggers Behavioral Monitor Agent.
    """
    incident = Incident(
        school_id=school_id,
        reported_by=current_user.id,
        **payload.model_dump()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Publish event → Behavioral Agent checks for patterns
    asyncio.create_task(
        publish_event(Events.INCIDENT_CREATED, {
            "school_id":    school_id,
            "student_id":   payload.student_id,
            "incident_id":  incident.id,
            "incident_type": payload.incident_type.value,
            "severity":     payload.severity.value,
        })
    )

    return incident


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    school_id:  int = Depends(get_current_school_id),
):
    q = db.query(Incident).filter(Incident.school_id == school_id)
    if student_id:
        q = q.filter(Incident.student_id == student_id)
    return q.order_by(Incident.incident_date.desc()).all()