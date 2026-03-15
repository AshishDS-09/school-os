# backend/app/models/attendance.py

from sqlalchemy import Column, Integer, ForeignKey, Date, String, Enum, Time
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin

class AttendanceStatus(str, enum.Enum):
    present  = "present"
    absent   = "absent"
    late     = "late"       # arrived but late
    excused  = "excused"    # excused absence (medical etc.)

class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    school_id  = Column(Integer, ForeignKey("schools.id"),  nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_id   = Column(Integer, ForeignKey("classes.id"),  nullable=False)
    # marked_by: the teacher's user_id who took attendance
    marked_by  = Column(Integer, ForeignKey("users.id"),    nullable=False)

    date       = Column(Date,              nullable=False)
    status     = Column(Enum(AttendanceStatus), nullable=False)
    # time_in: useful for late arrivals
    time_in    = Column(Time, nullable=True)
    notes      = Column(String(300), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="attendance")
    class_  = relationship("Class_",  back_populates="attendance")

    def __repr__(self):
        return f"<Attendance student={self.student_id} date={self.date} status={self.status}>"