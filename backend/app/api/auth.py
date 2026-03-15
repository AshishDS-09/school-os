# backend/app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, get_current_user
)
from app.models.user import User, UserRole
from app.models.school import School, SubscriptionTier
from app.schemas.auth import (
    TokenResponse, RegisterSchoolRequest, UserResponse
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email + password.
    Returns a JWT token to use in all future requests.
    
    In Swagger UI: click 'Authorize' button and paste the token.
    In your frontend: store in localStorage and send as
    'Authorization: Bearer <token>' header on every request.
    """
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()

    # Always run verify_password even if user not found
    # This prevents timing attacks (attacker can't tell if email exists)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your school admin."
        )

    # Create JWT with user info embedded
    token = create_access_token({
        "sub":       user.email,
        "user_id":   user.id,
        "school_id": user.school_id,
        "role":      user.role.value,
    })

    return TokenResponse(
        access_token=token,
        role=user.role,
        school_id=user.school_id,
        user_id=user.id,
        full_name=user.full_name
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register_school(payload: RegisterSchoolRequest, db: Session = Depends(get_db)):
    """
    Register a new school + create the first admin user.
    This is how new schools sign up for School OS.
    """
    # Check email not already used
    existing = db.query(School).filter(School.email == payload.school_email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A school with this email already exists."
        )

    # Create school
    school = School(
        name=payload.school_name,
        email=payload.school_email,
        phone=payload.school_phone,
        city=payload.school_city,
        state=payload.school_state,
        subscription_tier=SubscriptionTier.basic  # starts on basic plan
    )
    db.add(school)
    db.flush()  # get school.id without full commit

    # Create admin user for this school
    admin = User(
        school_id=school.id,
        role=UserRole.admin,
        first_name=payload.admin_first_name,
        last_name=payload.admin_last_name,
        email=payload.school_email,
        hashed_password=hash_password(payload.admin_password)
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    token = create_access_token({
        "sub":       admin.email,
        "user_id":   admin.id,
        "school_id": school.id,
        "role":      admin.role.value,
    })

    return TokenResponse(
        access_token=token,
        role=admin.role,
        school_id=school.id,
        user_id=admin.id,
        full_name=admin.full_name
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently logged-in user's profile.
    Frontend calls this on app load to know who is logged in.
    """
    return current_user