import logging
from contextlib import asynccontextmanager
from typing import Any

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import get_last_connection_error, test_connection
from app.limiter import limiter, rate_limit_exceeded_handler
from app.logging_config import setup_logging
from app.routers import funnel_projects, funnels, health, jobs, offers, users, webhooks, workflow_runs
from app.services.langfuse_client import init_langfuse

logger = logging.getLogger(__name__)

API_DESCRIPTION = """
OfferLaunch API powers funnel generation and builder workflows.

## Authentication
- Most endpoints require a Clerk JWT in `Authorization: Bearer <token>`.
- Public endpoints are limited to health checks and Clerk webhooks.

## Core flow
1. Create an offer with intake data.
2. Start a workflow run.
3. Track progress through jobs and SSE stream events.
4. Read and edit generated funnel project files.
"""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Service health and readiness probes.",
    },
    {
        "name": "webhooks",
        "description": "Inbound Clerk lifecycle webhooks.",
    },
    {
        "name": "users",
        "description": "Authenticated user profile and usage endpoints.",
    },
    {
        "name": "offers",
        "description": "Offer lifecycle management and intake payloads.",
    },
    {
        "name": "workflow-runs",
        "description": "Pipeline run orchestration and status retrieval.",
    },
    {
        "name": "jobs",
        "description": "Job status and real-time generation stream endpoints.",
    },
    {
        "name": "funnels",
        "description": "Funnel retrieval and metadata updates.",
    },
    {
        "name": "funnel-projects",
        "description": "Generated file tree storage and per-file updates.",
    },
]

PUBLIC_OPENAPI_PATHS = {"/health", "/health/detailed", "/webhooks/clerk"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.2,
            send_default_pii=False,
        )
        logger.info("Sentry initialized for FastAPI")

    langfuse_client = init_langfuse()
    if langfuse_client is not None:
        logger.info("Langfuse initialization attempted in FastAPI process")

    db_connected = await test_connection()
    if db_connected:
        logger.info("Database connected successfully")
    else:
        error_detail = get_last_connection_error() or "Unknown database error"
        logger.error("Database connection failed: %s", error_detail)
    yield


app = FastAPI(
    title="OfferLaunch API",
    summary="Backend API for OfferLaunch funnel generation",
    version="0.1.0",
    description=API_DESCRIPTION,
    contact={
        "name": "OfferLaunch Support",
        "email": "support@offerlaunch.com",
    },
    license_info={"name": "Proprietary"},
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

allowed_origins = ["http://localhost:3000", settings.FRONTEND_URL]
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(offers.router)
app.include_router(users.router)
app.include_router(workflow_runs.router)
app.include_router(jobs.router)
app.include_router(funnels.router)
app.include_router(funnel_projects.router)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        summary=app.summary,
        description=app.description,
        routes=app.routes,
    )

    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Clerk JWT sent as Authorization: Bearer <token>",
    }

    for path, methods in openapi_schema.get("paths", {}).items():
        if path in PUBLIC_OPENAPI_PATHS:
            continue

        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
