# backend/app/models/class_.py

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Class_(Base, TimestampMixin):
    __tablename__ = "classes"

    school_id        = Column(Integer, ForeignKey("schools.id"), nullable=False)
    # class_teacher_id links to the User who is the homeroom teacher
    class_teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    grade            = Column(String(20), nullable=False)   # e.g. "8", "9", "10"
    section          = Column(String(10), nullable=False)   # e.g. "A", "B", "C"
    academic_year    = Column(String(20), nullable=False)   # e.g. "2024-25"
    # subject_teachers: {"Math": 3, "Science": 7, "English": 12}
    # Stores teacher_id per subject as JSON
    subject_teachers = Column(String(500), default="{}")

    students      = relationship("Student",    back_populates="class_")
    class_teacher = relationship("User",       foreign_keys=[class_teacher_id])
    attendance    = relationship("Attendance", back_populates="class_")

    @property
    def display_name(self):
        return f"Grade {self.grade} - Section {self.section}"

    def __repr__(self):
        return f"<Class Grade{self.grade}-{self.section}>"