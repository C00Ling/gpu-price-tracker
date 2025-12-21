# jobs/celery_app.py
"""
Celery application for background tasks and scheduled scraping
"""
import os
from celery import Celery
from celery.schedules import crontab
from core.config import config
from core.logging import get_logger

logger = get_logger("celery")

# Get Celery configuration
broker_url = os.getenv("CELERY_BROKER_URL") or config.get("celery.broker_url", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND") or config.get("celery.result_backend", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "gpu_market",
    broker=broker_url,
    backend=result_backend,
    include=["jobs.tasks"]
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Scheduled tasks (Celery Beat)
app.conf.beat_schedule = {
    "scrape-olx-every-6-hours": {
        "task": "jobs.tasks.scheduled_scrape",
        "schedule": crontab(hour="*/6", minute=0),  # Every 6 hours
        "options": {"queue": "scraping"}
    },
    "cleanup-old-cache-daily": {
        "task": "jobs.tasks.cleanup_cache",
        "schedule": crontab(hour=3, minute=0),  # Every day at 3 AM
        "options": {"queue": "maintenance"}
    },
    "generate-stats-hourly": {
        "task": "jobs.tasks.update_stats_cache",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"queue": "stats"}
    },
    "check-price-drops-every-6-hours": {
        "task": "jobs.tasks.check_price_drops",
        "schedule": crontab(hour="*/6", minute=30),  # Every 6 hours (offset 30 min)
        "options": {"queue": "notifications"},
        "kwargs": {"threshold_percent": 10}
    },
}

logger.info(f"✅ Celery app configured - broker: {broker_url}")
