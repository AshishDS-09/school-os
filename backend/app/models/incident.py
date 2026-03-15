# backend/app/models/incident.py

from sqlalchemy import Column, Integer, ForeignKey, String, Text, Date, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin

class IncidentSeverity(str, enum.Enum):
    low    = "low"     # minor issue
    medium = "medium"  # requires teacher attention
    high   = "high"    # requires principal + counselor

class IncidentType(str, enum.Enum):
    bullying       = "bullying"
    fighting       = "fighting"
    cheating       = "cheating"
    disruptive     = "disruptive"
    absenteeism    = "absenteeism"
    property_damage = "property_damage"
    other          = "other"

class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    school_id    = Column(Integer, ForeignKey("schools.id"),  nullable=False)
    student_id   = Column(Integer, ForeignKey("students.id"), nullable=False)
    reported_by  = Column(Integer, ForeignKey("users.id"),    nullable=False)

    incident_type = Column(Enum(IncidentType), nullable=False)
    severity      = Column(Enum(IncidentSeverity), nullable=False)
    incident_date = Column(Date,   nullable=False)
    description   = Column(Text,   nullable=False)
    action_taken  = Column(Text,   nullable=True)
    # is_resolved: set to True once counselor/principal handles it
    is_resolved   = Column(Boolean, default=False)
    resolved_notes = Column(Text,  nullable=True)

    student = relationship("Student", back_populates="incidents")

    def __repr__(self):
        return f"<Incident {self.incident_type} severity={self.severity} student={self.student_id}>"