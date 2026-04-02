import ssl

import certifi
from celery import Celery

from app.config import settings

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
