from fastapi import APIRouter, Response

from app.config import settings
from app.database import get_last_connection_error, test_connection

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness check",
    description="Lightweight health endpoint used for uptime probes.",
)
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@router.head("/health", include_in_schema=False)
async def health_check_head() -> Response:
    return Response(status_code=200)


@router.get(
    "/health/detailed",
    summary="Detailed health check",
    description="Health endpoint including database connectivity diagnostics.",
)
async def health_check_detailed() -> dict[str, str]:
    db_connected = await test_connection()
    if db_connected:
        return {
            "status": "ok",
            "db": "connected",
            "environment": settings.ENVIRONMENT,
        }

    return {
        "status": "ok",
        "db": "error",
        "detail": get_last_connection_error() or "Unknown database error",
    }
