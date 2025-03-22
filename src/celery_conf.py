from celery import Celery

from .settings import settings

# Настройка Celery для работы с RabbitMQ
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,  # RabbitMQ (по умолчанию)
)


celery_app.autodiscover_tasks(["src.users"])
