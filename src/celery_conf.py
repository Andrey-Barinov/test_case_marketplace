from celery import Celery

from .settings import settings

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,  # RabbitMQ (по умолчанию)
)


celery_app.autodiscover_tasks(["src.users"])
