# backend/app/models/agent_state.py

from sqlalchemy import Column, Integer, ForeignKey, String, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base, TimestampMixin

class AgentState(Base, TimestampMixin):
    __tablename__ = "agent_state"

    school_id   = Column(Integer, ForeignKey("schools.id"),  nullable=False)
    student_id  = Column(Integer, ForeignKey("students.id"), nullable=True)
    # agent_name: which agent owns this state record
    agent_name  = Column(String(100), nullable=False)
    # entity_type: "student", "lead", "teacher", "class"
    entity_type = Column(String(50),  nullable=False)
    entity_id   = Column(Integer,     nullable=False)
    # last_run: when this agent last processed this entity
    last_run    = Column(DateTime,    nullable=True)
    # state_json: everything the agent needs to remember
    # Example for academic_agent:
    # {
    #   "risk_level": "HIGH",
    #   "last_alert_date": "2024-01-15",
    #   "previous_score_avg": 67.5,
    #   "alerted_count": 2,
    #   "weak_subjects": ["Mathematics", "Science"],
    #   "counselor_notified": false
    # }
    state_json  = Column(JSON, default={})

    # Relationship to student for easy joins
    student = relationship("Student", back_populates="agent_states")

    def __repr__(self):
        return f"<AgentState {self.agent_name} → {self.entity_type}#{self.entity_id}>"