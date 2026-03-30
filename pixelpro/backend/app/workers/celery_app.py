from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "pixelpro",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
    task_routes={
        "app.workers.tasks.enhance_image_task": {"queue": "enhancement"},
    },
    beat_schedule={
        "reset-monthly-credits": {
            "task": "app.workers.tasks.reset_all_monthly_credits",
            "schedule": 3600.0 * 24,
        }
    },
)
