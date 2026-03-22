import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import get_last_connection_error, test_connection
from app.routers import health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db_connected = await test_connection()
    if db_connected:
        logger.info("Database connected successfully")
    else:
        error_detail = get_last_connection_error() or "Unknown database error"
        logger.error("Database connection failed: %s", error_detail)
    yield


app = FastAPI(title="OfferLaunch API", lifespan=lifespan)

allowed_origins = ["http://localhost:3000", settings.FRONTEND_URL]
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
