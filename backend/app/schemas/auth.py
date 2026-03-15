# backend/app/schemas/auth.py

from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterSchoolRequest(BaseModel):
    # School info
    school_name: str
    school_email: EmailStr
    school_phone: str
    school_city: str
    school_state: str
    # First admin user
    admin_first_name: str
    admin_last_name: str
    admin_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    school_id: int
    user_id: int
    full_name: str

class UserResponse(BaseModel):
    id: int
    school_id: int
    role: UserRole
    first_name: str
    last_name: str
    email: str
    phone: str | None
    is_active: bool

    class Config:
        from_attributes = True   # allows reading from SQLAlchemy model directly