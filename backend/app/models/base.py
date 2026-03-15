# backend/app/models/base.py

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    """
    Add this to any model to get id, created_at, updated_at for free.
    Every table in this project uses this mixin.
    """
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )