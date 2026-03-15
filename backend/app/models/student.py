# backend/app/models/student.py

from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Student(Base, TimestampMixin):
    __tablename__ = "students"

    school_id   = Column(Integer, ForeignKey("schools.id"),  nullable=False)
    class_id    = Column(Integer, ForeignKey("classes.id"),  nullable=False)
    # parent_id links to a User with role='parent'
    parent_id   = Column(Integer, ForeignKey("users.id"),    nullable=True)

    first_name  = Column(String(100), nullable=False)
    last_name   = Column(String(100), nullable=False)
    roll_number = Column(String(20),  nullable=False)
    date_of_birth = Column(Date,      nullable=True)
    gender      = Column(String(10))
    phone       = Column(String(20))   # student's own phone (optional)
    address     = Column(String(500))
    is_active   = Column(Boolean, default=True)
    # photo_url: stored in Supabase Storage
    photo_url   = Column(String(500), nullable=True)

    # Relationships
    school      = relationship("School",  back_populates="students")
    class_      = relationship("Class_",  back_populates="students")
    parent      = relationship("User",    back_populates="student",
                               foreign_keys=[parent_id])
    attendance  = relationship("Attendance",        back_populates="student")
    marks       = relationship("Marks",             back_populates="student")
    fee_records = relationship("FeeRecord",         back_populates="student")
    agent_states = relationship("AgentState",       back_populates="student")
    incidents   = relationship("Incident",          back_populates="student")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Student {self.full_name} Roll#{self.roll_number}>"