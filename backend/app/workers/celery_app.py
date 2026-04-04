import ssl
import logging

import certifi
import sentry_sdk
from celery import Celery, signals
from sentry_sdk.integrations.celery import CeleryIntegration

from app.config import settings
from app.logging_config import setup_logging
from app.services.langfuse_client import init_langfuse

logger = logging.getLogger(__name__)

celery_app = Celery("offerlaunch")

ssl_options = {
    "ssl_cert_reqs": ssl.CERT_REQUIRED,
    "ssl_ca_certs": certifi.where(),
}

celery_app.config_from_object(
    {
        "broker_url": settings.CELERY_BROKER_URL,
        "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "task_track_started": True,
        "task_ignore_result": True,
        "task_store_errors_even_if_ignored": True,
        "broker_connection_retry_on_startup": True,
        "broker_use_ssl": ssl_options,
        "redis_backend_use_ssl": ssl_options,
        "result_backend_transport_options": {
            "ssl_cert_reqs": ssl.CERT_REQUIRED,
            "ssl_ca_certs": certifi.where(),
        },
        "broker_transport_options": {
            "visibility_timeout": 3600,
        },
        "imports": ["app.workers.tasks"],
    }
)


@signals.celeryd_init.connect
def _initialize_worker_observability(*args, **kwargs) -> None:
    _ = (args, kwargs)
    setup_logging()

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.2,
            send_default_pii=False,
            integrations=[CeleryIntegration(propagate_traces=True)],
        )
        logger.info("Sentry initialized for Celery worker")

    langfuse_client = init_langfuse()
    if langfuse_client is not None:
        logger.info("Langfuse initialization attempted in Celery worker")
