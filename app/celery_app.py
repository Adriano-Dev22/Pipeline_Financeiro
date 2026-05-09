from celery import Celery
from app.config import settings

celery_app = Celery(
    "asyncledger",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.charge_worker"],
)


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_routes={
        "app.workers.charge_worker.process_charge": {"queue": "charges"},
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
