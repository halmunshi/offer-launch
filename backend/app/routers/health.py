from fastapi import APIRouter

from app.config import settings
from app.database import get_last_connection_error, test_connection

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@router.get("/health/detailed")
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
