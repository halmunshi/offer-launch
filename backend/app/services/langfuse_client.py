import logging
import os
import importlib
import base64
from typing import Any

from langfuse import get_client

from app.config import settings

logger = logging.getLogger(__name__)

_langfuse_client: Any | None = None
_claude_sdk_instrumented = False


def _configure_claude_sdk_instrumentation() -> bool:
    try:
        module = importlib.import_module("langsmith.integrations.claude_agent_sdk")
        configure_fn = getattr(module, "configure_claude_agent_sdk", None)
        if not callable(configure_fn):
            logger.warning(
                "langsmith integration loaded but configure_claude_agent_sdk is missing"
            )
            return False
        configure_fn()
        return True
    except ModuleNotFoundError:
        logger.warning(
            "Claude Agent SDK instrumentation bridge is unavailable in this "
            "langsmith version. Continuing without Claude-SDK auto-instrumentation."
        )
        return False
    except Exception:
        logger.exception("Failed to configure Claude Agent SDK instrumentation")
        return False


def _ensure_langfuse_env() -> None:
    if settings.LANGFUSE_PUBLIC_KEY and not os.environ.get("LANGFUSE_PUBLIC_KEY"):
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    if settings.LANGFUSE_SECRET_KEY and not os.environ.get("LANGFUSE_SECRET_KEY"):
        os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    if settings.LANGFUSE_BASE_URL and not os.environ.get("LANGFUSE_BASE_URL"):
        os.environ["LANGFUSE_BASE_URL"] = settings.LANGFUSE_BASE_URL

    os.environ.setdefault("LANGSMITH_OTEL_ENABLED", "true")
    os.environ.setdefault("LANGSMITH_OTEL_ONLY", "true")
    os.environ.setdefault("LANGSMITH_TRACING", "true")

    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY and settings.LANGFUSE_BASE_URL:
        endpoint = settings.LANGFUSE_BASE_URL.rstrip("/") + "/api/public/otel"
        auth = f"{settings.LANGFUSE_PUBLIC_KEY}:{settings.LANGFUSE_SECRET_KEY}"
        auth_b64 = base64.b64encode(auth.encode("utf-8")).decode("utf-8")

        os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", endpoint)
        os.environ.setdefault(
            "OTEL_EXPORTER_OTLP_HEADERS",
            f"Authorization=Basic%20{auth_b64},x-langfuse-ingestion-version=4",
        )
        os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")


def init_langfuse() -> Any | None:
    global _langfuse_client
    global _claude_sdk_instrumented

    if _langfuse_client is not None:
        return _langfuse_client

    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.warning("Langfuse keys not set; skipping Langfuse initialization")
        return None

    _ensure_langfuse_env()

    try:
        client = get_client()
        try:
            auth_ok = client.auth_check()
        except Exception:
            logger.exception("Langfuse auth check failed")
            auth_ok = False

        if auth_ok:
            logger.info("Langfuse initialized and authenticated")
        else:
            logger.warning("Langfuse initialized but auth check did not pass")

        if not _claude_sdk_instrumented:
            try:
                configured = _configure_claude_sdk_instrumentation()
                if configured:
                    _claude_sdk_instrumented = True
                    logger.info("Claude Agent SDK instrumentation configured for Langfuse")
            except Exception:
                logger.exception("Unexpected error while configuring Claude SDK instrumentation")

        _langfuse_client = client
        return _langfuse_client
    except Exception:
        logger.exception("Failed to initialize Langfuse client")
        return None


def get_langfuse() -> Any | None:
    return _langfuse_client
