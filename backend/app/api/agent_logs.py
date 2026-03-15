# backend/app/api/agent_logs.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_school_id
from app.models.agent_log import AgentLog, AgentOutcome

router = APIRouter(prefix="/api/agent-logs", tags=["Agent Logs"])

class AgentLogResponse(BaseModel):
    id: int
    agent_name: str
    trigger: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    action_taken: Optional[str]
    outcome: AgentOutcome
    error_message: Optional[str]
    duration_ms: Optional[int]
    cost_usd: float
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("", response_model=List[AgentLogResponse])
def list_agent_logs(
    agent_name: Optional[str] = Query(None),
    outcome:    Optional[str] = Query(None),
    limit:      int           = Query(50, le=200),
    db: Session = Depends(get_db),
    school_id:  int = Depends(get_current_school_id),
):
    """
    Get recent agent activity for the admin dashboard.
    This powers the live agent activity feed on the frontend.
    """
    q = db.query(AgentLog).filter(AgentLog.school_id == school_id)
    if agent_name: q = q.filter(AgentLog.agent_name == agent_name)
    if outcome:    q = q.filter(AgentLog.outcome    == outcome)
    return q.order_by(AgentLog.created_at.desc()).limit(limit).all()