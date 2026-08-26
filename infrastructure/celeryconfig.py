from celery import Celery

app = Celery("riskshield")

app.conf.update(
    broker_url="redis://redis:6379/0",
    result_backend="redis://redis:6379/1",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_routes={
        "ml.tasks.*": {"queue": "ml"},
        "monitoring.tasks.*": {"queue": "monitoring"},
    },
    task_default_queue="default",
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 3600,
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
    rate_limits={
        "ml.tasks.predict": "100/m",
        "ml.tasks.retrain": "1/h",
        "monitoring.tasks.collect_metrics": "60/m",
        "monitoring.tasks.check_drift": "10/m",
    },
)

app.autodiscover_tasks(["ml", "monitoring"])
