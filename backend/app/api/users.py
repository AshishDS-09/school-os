from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import AdminOnly, get_current_school_id, hash_password
from app.models.user import User, UserRole
from app.schemas.user_management import ManagedUserCreate, ManagedUserResponse

router = APIRouter(prefix="/api/users", tags=["User Management"])


@router.get("", response_model=list[ManagedUserResponse])
def list_users(
    role: UserRole | None = Query(None),
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=AdminOnly,
):
    query = db.query(User).filter(User.school_id == school_id)
    if role is not None:
        query = query.filter(User.role == role)

    return query.order_by(User.role, User.first_name, User.last_name).all()


@router.post("", response_model=ManagedUserResponse, status_code=201)
def create_user(
    payload: ManagedUserCreate,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school_id),
    _=AdminOnly,
):
    if payload.role not in {UserRole.teacher, UserRole.parent}:
        raise HTTPException(
            status_code=400,
            detail="Admins can only create teacher or parent accounts from this endpoint.",
        )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    user = User(
        school_id=school_id,
        role=payload.role,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        phone=payload.phone,
        language=payload.language or "en",
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
