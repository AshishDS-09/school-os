# backend/app/tasks/__init__.py

from celery import Celery
import os

celery_app = Celery(
    "school_os",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
    include=[]  # agents will be added here in Phase 5
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# This is crucial — import task modules so Celery registers them.
from app.tasks import agent_tasks, notification_tasks

