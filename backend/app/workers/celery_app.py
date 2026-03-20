"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sliples",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks", "app.workers.scheduled"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Fair distribution for long tasks
    result_expires=86400,  # Results expire after 24 hours
)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-expired-runs": {
        "task": "app.workers.scheduled.cleanup_expired_runs",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "cleanup-orphaned-screenshots": {
        "task": "app.workers.scheduled.cleanup_orphaned_screenshots",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}
