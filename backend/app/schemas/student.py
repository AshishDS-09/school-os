# backend/app/schemas/student.py

from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.models.student import Student

class StudentCreate(BaseModel):
    """Fields required when creating a new student"""
    class_id: int
    parent_id: Optional[int] = None
    first_name: str
    last_name: str
    roll_number: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class StudentUpdate(BaseModel):
    """All fields optional — only send what you want to change"""
    class_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roll_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class StudentResponse(BaseModel):
    """What the API returns when you request student data"""
    id: int
    school_id: int
    class_id: int
    parent_id: Optional[int]
    first_name: str
    last_name: str
    roll_number: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    phone: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True