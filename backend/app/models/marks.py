# backend/app/models/marks.py

from sqlalchemy import Column, Integer, ForeignKey, String, Float, Date, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin

class ExamType(str, enum.Enum):
    unit_test    = "unit_test"
    midterm      = "midterm"
    final        = "final"
    assignment   = "assignment"
    quiz         = "quiz"
    practical    = "practical"

class Marks(Base, TimestampMixin):
    __tablename__ = "marks"

    school_id   = Column(Integer, ForeignKey("schools.id"),  nullable=False)
    student_id  = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_id    = Column(Integer, ForeignKey("classes.id"),  nullable=False)
    entered_by  = Column(Integer, ForeignKey("users.id"),    nullable=False)

    subject     = Column(String(100), nullable=False)  # "Mathematics", "Science"
    exam_type   = Column(Enum(ExamType), nullable=False)
    exam_date   = Column(Date, nullable=False)
    score       = Column(Float, nullable=False)   # actual marks scored
    max_score   = Column(Float, nullable=False)   # out of how many
    # Computed: score/max_score * 100
    # Not stored — calculated on the fly to stay accurate

    remarks     = Column(String(300), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="marks")

    @property
    def percentage(self):
        if self.max_score == 0:
            return 0
        return round((self.score / self.max_score) * 100, 2)

    def __repr__(self):
        return f"<Marks {self.subject} {self.exam_type} {self.percentage}%>"