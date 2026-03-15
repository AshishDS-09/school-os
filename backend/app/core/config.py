# backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://schooladmin:schoolpass123@localhost:5432/schoolos"

    # Redis — use 'localhost' when running alembic/scripts locally
    # Docker services use 'redis' as hostname (set in .env)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # OpenAI
    OPENAI_API_KEY: str = ""
    
     # ── Supabase ─────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Celery
    CELERY_BROKER_URL: str  = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str  = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # SendGrid
    SENDGRID_API_KEY: str   = ""
    SENDGRID_FROM_EMAIL: str = "noreply@schoolos.in"

    # App
    APP_NAME: str = "School OS"
    DEBUG: bool   = True

    class Config:
        env_file = ".env"
        extra = "ignore"   # ignore unknown keys in .env

settings = Settings()


   

 