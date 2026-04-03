# backend/app/core/tenant.py

import logging
from typing import Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class TenantContext:
    """
    Thread-local storage for the current request's school_id.

    Why this exists:
        Every API request is authenticated with a JWT that contains school_id.
        We store that school_id here at the start of each request.
        Every service and agent can then read it without passing it everywhere.

    Usage:
        # In a FastAPI dependency (set it once per request):
        TenantContext.set(school_id)

        # Anywhere in the codebase (read it):
        school_id = TenantContext.get()
    """
    _school_id: Optional[int] = None

    @classmethod
    def set(cls, school_id: int) -> None:
        cls._school_id = school_id

    @classmethod
    def get(cls) -> int:
        if cls._school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context not set. Are you authenticated?"
            )
        return cls._school_id

    @classmethod
    def clear(cls) -> None:
        cls._school_id = None

    @classmethod
    def is_set(cls) -> bool:
        return cls._school_id is not None