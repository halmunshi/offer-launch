import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import get_last_connection_error, test_connection
from app.limiter import limiter, rate_limit_exceeded_handler
from app.routers import funnel_projects, funnels, health, jobs, offers, users, webhooks, workflow_runs

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
