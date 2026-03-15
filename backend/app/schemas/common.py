# backend/app/schemas/common.py
# Reusable pieces used across multiple schemas

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Generic, TypeVar, List

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard wrapper for list endpoints.
    Every list endpoint returns:  { items: [...], total: 42, page: 1, size: 20 }
    """
    items: List[T]
    total: int
    page: int
    size: int

class MessageResponse(BaseModel):
    """Simple success message response"""
    message: str
    success: bool = True