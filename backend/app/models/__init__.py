# backend/app/models/__init__.py

from app.models.base import Base, TimestampMixin
from app.models.school import School
from app.models.user import User
from app.models.student import Student
from app.models.class_ import Class_
from app.models.attendance import Attendance
from app.models.marks import Marks
from app.models.assignment import Assignment
from app.models.fee import FeeRecord
from app.models.notification import Notification
from app.models.notif_queue import NotificationQueue
from app.models.agent_log import AgentLog
from app.models.agent_state import AgentState
from app.models.incident import Incident
from app.models.lead import Lead

# This list tells Alembic which models exist
__all__ = [
    "Base", "School", "User", "Student", "Class_",
    "Attendance", "Marks", "Assignment", "FeeRecord",
    "Notification", "NotificationQueue", "AgentLog",
    "AgentState", "Incident", "Lead"
]