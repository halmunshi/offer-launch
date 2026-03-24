from celery import Celery

from app.config import settings


def _broker_url() -> str:
    return settings.CELERY_BROKER_URL or "redis://localhost:6379/0"


def _result_backend() -> str:
    return settings.CELERY_RESULT_BACKEND or _broker_url()


celery_app = Celery(
    "offerlaunch",
    broker=_broker_url(),
    backend=_result_backend(),
)
