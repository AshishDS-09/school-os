# backend/app/models/agent_log.py

from sqlalchemy import Column, Integer, ForeignKey, String, Text, Float, Enum
import enum
from app.models.base import Base, TimestampMixin

class AgentOutcome(str, enum.Enum):
    success = "success"
    error   = "error"
    skipped = "skipped"   # agent ran but decided no action needed

class AgentLog(Base, TimestampMixin):
    __tablename__ = "agent_logs"

    school_id    = Column(Integer, ForeignKey("schools.id"), nullable=False)
    # agent_name: "academic_agent", "attendance_agent", "fee_agent" etc.
    agent_name   = Column(String(100), nullable=False)
    # trigger: "event" (fired by Redis event) or "cron" (scheduled run)
    trigger      = Column(String(50),  nullable=False)
    # entity_type + entity_id: what the agent acted on
    entity_type  = Column(String(50),  nullable=True)   # "student", "lead"
    entity_id    = Column(Integer,     nullable=True)   # student_id, lead_id etc.
    # action_taken: human-readable description of what the agent did
    action_taken = Column(Text,        nullable=True)
    outcome      = Column(Enum(AgentOutcome), default=AgentOutcome.success)
    error_message = Column(Text,       nullable=True)
    # duration_ms: how long the agent took to run
    duration_ms  = Column(Integer,     nullable=True)
    # cost_usd: OpenAI API cost for this run — track weekly to control spend
    cost_usd     = Column(Float,       default=0.0)

    def __repr__(self):
        return f"<AgentLog {self.agent_name} → {self.outcome} ({self.duration_ms}ms)>"