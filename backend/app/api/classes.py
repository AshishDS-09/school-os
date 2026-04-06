from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import AdminOnly, get_current_school_id
from app.models.class_ import Class_
from app.models.user import User, UserRole
from app.schemas.class_ import ClassCreate, ClassResponse

router = APIRouter(prefix="/api/classes", tags=["Classes"])


@router.get("", response_model=list[ClassResponse])
def list_classes(
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=AdminOnly,
):
    return (
        db.query(Class_)
        .filter(Class_.school_id == school_id)
        .order_by(Class_.grade, Class_.section)
        .all()
    )


@router.post("", response_model=ClassResponse, status_code=201)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=AdminOnly,
):
    if payload.class_teacher_id is not None:
        teacher = (
            db.query(User)
            .filter(
                User.id == payload.class_teacher_id,
                User.school_id == school_id,
                User.role == UserRole.teacher,
            )
            .first()
        )
        if not teacher:
            raise HTTPException(status_code=400, detail="Selected class teacher was not found.")

    existing = (
        db.query(Class_)
        .filter(
            Class_.school_id == school_id,
            Class_.grade == payload.grade,
            Class_.section == payload.section,
            Class_.academic_year == payload.academic_year,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="This class already exists for the academic year.")

    class_ = Class_(school_id=school_id, **payload.model_dump())
    db.add(class_)
    db.commit()
    db.refresh(class_)
    return class_
