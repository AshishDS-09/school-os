# backend/app/models/assignment.py

from sqlalchemy import Column, Integer, ForeignKey, String, Date, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    school_id    = Column(Integer, ForeignKey("schools.id"),  nullable=False)
    class_id     = Column(Integer, ForeignKey("classes.id"),  nullable=False)
    created_by   = Column(Integer, ForeignKey("users.id"),    nullable=False)

    title        = Column(String(300), nullable=False)
    subject      = Column(String(100), nullable=False)
    description  = Column(String(1000), nullable=True)
    due_date     = Column(Date, nullable=False)
    max_marks    = Column(Integer, default=10)
    # submitted_student_ids: list of student IDs who submitted
    # e.g. [1, 4, 7, 12] — stored as JSON array
    submitted_student_ids = Column(JSON, default=[])
    is_active    = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Assignment {self.title} due={self.due_date}>"