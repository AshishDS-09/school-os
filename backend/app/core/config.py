# # backend/app/core/config.py

# from pydantic import field_validator
# from pydantic_settings import BaseSettings
# from typing import Optional

# class Settings(BaseSettings):
#     # Database
#     DATABASE_URL: str = "postgresql://schooladmin:schoolpass123@localhost:5432/schoolos"

#     # Redis — use 'localhost' when running alembic/scripts locally
#     # Docker services use 'redis' as hostname (set in .env)
#     REDIS_URL: str = "redis://localhost:6379/0"

#     # Security
#     SECRET_KEY: str = "dev-secret-key-change-in-production"
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

#     # Gemini
#     GEMINI_API_KEY: str = ""
    
#      # ── Supabase ─────────────────────────
#     SUPABASE_URL: str = ""
#     SUPABASE_ANON_KEY: str = ""
#     SUPABASE_SERVICE_KEY: str = ""

#     # Celery
#     CELERY_BROKER_URL: str  = "redis://redis:6379/1"
#     CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

#     # Twilio
#     TWILIO_ACCOUNT_SID: str = ""
#     TWILIO_AUTH_TOKEN: str  = ""
#     TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

#     # SendGrid
#     SENDGRID_API_KEY: str   = ""
#     SENDGRID_FROM_EMAIL: str = "noreply@schoolos.in"

#     # App
#     APP_NAME: str = "School OS"
#     DEBUG: bool   = True
    
#     # Add these 3 lines to the Settings class:
#     RAZORPAY_KEY_ID: str = ""
#     RAZORPAY_KEY_SECRET: str = ""
#     RAZORPAY_WEBHOOK_SECRET: str = ""

#     @field_validator("DEBUG", mode="before")
#     @classmethod
#     def normalize_debug(cls, value):
#         if isinstance(value, str):
#             normalized = value.strip().lower()
#             if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
#                 return False
#             if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
#                 return True
#         return value

#     class Config:
#         env_file = ("backend/.env", ".env")
#         extra = "ignore"   # ignore unknown keys in .env

# settings = Settings()
# backend/app/core/config.py — final production version

from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ── Environment ─────────────────────────────────
    ENVIRONMENT: str = "development"   # "production" on Railway

    # ── Database ─────────────────────────────────────
    # In production: Railway injects DATABASE_URL automatically
    DATABASE_URL: str = "postgresql://schooladmin:schoolpass123@localhost:5432/schoolos"

    # ── Redis ─────────────────────────────────────────
    # In production: Upstash Redis URL from Railway env var
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security ──────────────────────────────────────
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── Gemini ────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── Supabase ──────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # ── Twilio ────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # ── SendGrid ──────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@yourschool.com"

    # ── Celery ────────────────────────────────────────
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # ── Razorpay ──────────────────────────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── CORS ──────────────────────────────────────────
    # Comma-separated list of allowed frontend origins
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── App ───────────────────────────────────────────
    APP_NAME: str = "School OS"
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
                return True
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_origin_regex(self) -> str:
        # Allow Vercel production and preview deployments unless explicitly restricted elsewhere.
        return r"^https://.*\.vercel\.app$"

    @property
    def celery_broker_url(self) -> str:
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        return self.REDIS_URL.replace("/0", "/1") if self.REDIS_URL.endswith("/0") else self.REDIS_URL

    @property
    def celery_result_backend(self) -> str:
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        return self.REDIS_URL.replace("/0", "/2") if self.REDIS_URL.endswith("/0") else self.REDIS_URL

    @property
    def billing_enabled(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

   

 
