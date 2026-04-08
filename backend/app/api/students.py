# backend/app/api/students.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.security import get_current_school_id, TeacherOrAdmin
from app.models.class_ import Class_
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services.cache_service import (
    cache_get, cache_set, cache_invalidate, make_cache_key, CACHE_TTL
)

router = APIRouter(prefix="/api/students", tags=["Students"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[StudentResponse])
async def list_students(
    class_id: Optional[int] = Query(None, description="Filter by class"),
    is_active: Optional[bool] = Query(True, description="Filter active/inactive"),
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    current_user: User = Depends(__import__(
        "app.core.security", fromlist=["get_current_user"]
    ).get_current_user),
):
    """
    Get all students for the logged-in user's school.
    
    ALWAYS filters by school_id — a teacher from school A
    can never see students from school B.
    Results are cached in Redis for 5 minutes.
    """
    # Build cache key that includes all filter params
    cache_key = make_cache_key("students", school_id, class_id or "all", is_active)

    # Try cache first
    try:
        cached = await cache_get(cache_key)
        if cached:
            return cached
    except Exception as exc:
        logger.warning("Cache read failed for key %s: %s", cache_key, exc)

    # Cache miss — hit the database
    query = db.query(Student).filter(Student.school_id == school_id)

    if current_user.role == UserRole.parent:
        query = query.filter(Student.parent_id == current_user.id)

    if class_id is not None:
        query = query.filter(Student.class_id == class_id)
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)

    students = query.order_by(Student.first_name).all()

    # Serialise to dict for caching (Pydantic model → dict)
    result = [StudentResponse.from_orm(s).model_dump() for s in students]

    # Store in cache
    try:
        await cache_set(cache_key, result, CACHE_TTL["student_list"])
    except Exception as exc:
        logger.warning("Cache write failed for key %s: %s", cache_key, exc)

    return result


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    current_user: User = Depends(get_current_user_dep := __import__(
        'app.core.security', fromlist=['get_current_user']
    ).get_current_user)
):
    """Get a single student by ID."""
    # Parents can only see their own child
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Extra check: parents can only access their own child's data
    if current_user.role == UserRole.parent and student.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return student


@router.post("", response_model=StudentResponse, status_code=201)
async def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin
):
    """Create a new student. Only teachers and admins can do this."""
    class_ = db.query(Class_).filter(
        Class_.id == payload.class_id,
        Class_.school_id == school_id
    ).first()
    if not class_:
        raise HTTPException(status_code=400, detail="Selected class was not found in your school.")

    if payload.parent_id is not None:
        parent = db.query(User).filter(
            User.id == payload.parent_id,
            User.school_id == school_id,
            User.role == UserRole.parent
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Selected parent account was not found.")

    student = Student(school_id=school_id, **payload.model_dump())
    try:
        db.add(student)
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Could not create student due to invalid linked records."
        )

    # Invalidate cached student lists for this school
    try:
        await cache_invalidate(f"students:{school_id}:*")
    except Exception as exc:
        logger.warning("Cache invalidate failed for school_id=%s: %s", school_id, exc)

    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin
):
    """Update a student's details."""
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    updates = payload.model_dump(exclude_unset=True)
    if "class_id" in updates:
        class_ = db.query(Class_).filter(
            Class_.id == updates["class_id"],
            Class_.school_id == school_id
        ).first()
        if not class_:
            raise HTTPException(status_code=400, detail="Selected class was not found in your school.")

    # Only update fields that were actually sent (exclude_unset=True)
    for field, value in updates.items():
        setattr(student, field, value)

    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Could not update student due to invalid linked records."
        )

    # Clear all cached student data for this school
    try:
        await cache_invalidate(f"students:{school_id}:*")
    except Exception as exc:
        logger.warning("Cache invalidate failed for school_id=%s: %s", school_id, exc)

    return student


@router.delete("/{student_id}")
async def deactivate_student(
    student_id: int,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=Depends(__import__('app.core.security', fromlist=['require_role'])
              .require_role(__import__('app.models.user', fromlist=['UserRole']).UserRole.admin))
):
    """
    Deactivate a student (soft delete — data is kept, student is hidden).
    Only admins can do this.
    """
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_active = False
    db.commit()
    try:
        await cache_invalidate(f"students:{school_id}:*")
    except Exception as exc:
        logger.warning("Cache invalidate failed for school_id=%s: %s", school_id, exc)
    return {"message": f"Student {student.full_name} deactivated successfully"}
