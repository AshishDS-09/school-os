# backend/app/models/user.py

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin

class UserRole(str, enum.Enum):
    admin   = "admin"    # Full access — school principal/owner
    teacher = "teacher"  # Access to their class only
    parent  = "parent"   # Read-only — their child only
    student = "student"  # Read-only — own data only

class User(Base, TimestampMixin):
    __tablename__ = "users"

    school_id       = Column(Integer, ForeignKey("schools.id"), nullable=False)
    role            = Column(Enum(UserRole), nullable=False)
    first_name      = Column(String(100), nullable=False)
    last_name       = Column(String(100), nullable=False)
    email           = Column(String(200), unique=True, nullable=False)
    phone           = Column(String(20))
    hashed_password = Column(String(255), nullable=False)
    is_active       = Column(Boolean, default=True)
    # Preferred language for notifications: 'en', 'hi', 'mr', 'ta', etc.
    language        = Column(String(10), default="en")

    # Relationships
    school  = relationship("School", back_populates="users")
    student = relationship("Student", back_populates="parent", uselist=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"