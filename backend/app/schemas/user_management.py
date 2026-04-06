from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class ManagedUserCreate(BaseModel):
    role: UserRole
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    language: str | None = "en"


class ManagedUserResponse(BaseModel):
    id: int
    school_id: int
    role: UserRole
    first_name: str
    last_name: str
    email: str
    phone: str | None
    language: str | None
    is_active: bool

    class Config:
        from_attributes = True
