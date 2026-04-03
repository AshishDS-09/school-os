# backend/app/core/security.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.core.tenant import TenantContext

# bcrypt is the gold standard for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use plain HTTP Bearer auth for protected endpoints.
# This keeps runtime auth simple and avoids Swagger's password-flow popup issues.
bearer_scheme = HTTPBearer()


# ── Password helpers ────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Turn 'mypassword123' into '$2b$12$...' (bcrypt hash)"""
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a plain password matches the stored hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT token helpers ───────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token that encodes user info.
    The token payload will look like:
    {
        "sub": "user@email.com",
        "school_id": 1,
        "role": "teacher",
        "user_id": 42,
        "exp": 1234567890   ← expiry timestamp
    }
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode a JWT and return its payload dict"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ── FastAPI Dependencies (inject into routes) ───────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency: extracts and validates the JWT from the request header.
    Raises 401 if token is missing, expired, or invalid.
    
    Usage in route:
        def my_route(current_user: User = Depends(get_current_user)):
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    TenantContext.set(user.school_id)
    return user


def get_current_school_id(
    current_user: User = Depends(get_current_user)
) -> int:
    """
    Dependency: returns just the school_id from the logged-in user.
    Add to ANY route that needs to filter by school — which is all of them.
    
    Usage:
        def my_route(school_id: int = Depends(get_current_school_id)):
    """
    return current_user.school_id


# ── Role guard factory ──────────────────────────────────────────────

def require_role(*allowed_roles: UserRole):
    """
    Factory that creates a role-checking dependency.
    
    Usage:
        @router.delete("/students/{id}")
        def delete_student(
            current_user: User = Depends(require_role(UserRole.admin))
        ):
    """
    def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return _check_role


# ── Convenience role shortcuts ──────────────────────────────────────
# Use these in routes instead of writing require_role() every time

AdminOnly    = Depends(require_role(UserRole.admin))
TeacherOrAdmin = Depends(require_role(UserRole.teacher, UserRole.admin))
AnyStaff     = Depends(require_role(UserRole.admin, UserRole.teacher))
AnyUser      = Depends(get_current_user)
