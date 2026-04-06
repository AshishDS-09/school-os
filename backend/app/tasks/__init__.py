# backend/app/tasks/__init__.py

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "school_os",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
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

