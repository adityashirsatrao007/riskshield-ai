import os
from celery import Celery

app = Celery("riskshield")

app.conf.update(
    broker_url=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_default_queue="default",
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    task_default_rate_limit="100/m",
)
