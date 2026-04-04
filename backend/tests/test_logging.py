import json
import logging
import sys

from app.config import settings
from app.logging_config import JSONFormatter, setup_logging


def test_json_formatter_includes_core_and_extra_fields() -> None:
    logger = logging.getLogger("offerlaunch.test")

    try:
        raise ValueError("boom")
    except ValueError:
        record = logger.makeRecord(
            name="offerlaunch.test",
            level=logging.ERROR,
            fn="test_logging.py",
            lno=10,
            msg="Pipeline failed",
            args=(),
            exc_info=sys.exc_info(),
            extra={
                "workflow_run_id": "wr-123",
                "funnel_id": "fu-456",
                "duration_ms": 321,
                "status": "error",
            },
        )

    payload = json.loads(JSONFormatter().format(record))

    assert payload["level"] == "ERROR"
    assert payload["logger"] == "offerlaunch.test"
    assert payload["message"] == "Pipeline failed"
    assert payload["environment"] == settings.ENVIRONMENT
    assert payload["workflow_run_id"] == "wr-123"
    assert payload["funnel_id"] == "fu-456"
    assert payload["duration_ms"] == 321
    assert payload["status"] == "error"
    assert "exc_info" in payload


def test_setup_logging_uses_plain_formatter_in_development(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    setup_logging()

    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 1
    formatter = root_logger.handlers[0].formatter
    assert formatter is not None
    assert type(formatter) is logging.Formatter


def test_setup_logging_uses_json_formatter_outside_development(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    setup_logging()

    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 1
    formatter = root_logger.handlers[0].formatter
    assert isinstance(formatter, JSONFormatter)
