import json
import logging
import uuid
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.middleware.clerk_auth import get_current_user
from app.models.enums import AgentType, JobStatus
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _sse_line(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _should_close_stream(event: dict, stream_agent_type: AgentType) -> bool:
    event_type = str(event.get("type", "")).lower()
    event_status = str(event.get("status", "")).lower()
    stage = str(event.get("stage", "")).lower()

    if event_status in {"done", "error"} and stage in {"", "funnel_builder", "copywriter"}:
        return True

    if stream_agent_type == AgentType.funnel_builder:
        return stage == "funnel_builder" and (
            event.get("done") is True or event_type in {"done", "error"}
        )

    if stream_agent_type == AgentType.copywriter:
        return stage == "copywriter" and (
            event.get("done") is True or event_type in {"done", "error"}
        )

    return event.get("done") is True or event_type in {"done", "error"}


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Job:
    result = await db.execute(
        select(Job).where(
            Job.id == job_id,
            Job.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.get("/{job_id}/stream")
async def stream_job(
    job_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    channel = f"job:{job_id}"

    async def event_generator() -> AsyncGenerator[str, None]:
        redis_client = None
        pubsub = None

        try:
            # Phase 1: ownership check before any Redis subscription.
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Job).where(
                        Job.id == job_id,
                        Job.user_id == current_user.id,
                    )
                )
                job = result.scalar_one_or_none()

                copywriter_job = None
                if job is not None and job.agent_type == AgentType.funnel_builder:
                    copywriter_result = await db.execute(
                        select(Job).where(
                            Job.workflow_run_id == job.workflow_run_id,
                            Job.user_id == current_user.id,
                            Job.agent_type == AgentType.copywriter,
                        )
                    )
                    copywriter_job = copywriter_result.scalar_one_or_none()

            if job is None:
                yield _sse_line({"type": "error", "message": "Job not found", "done": True})
                return

            # Phase 2: catch up from Neon.
            progress_events: list[dict] = []

            if copywriter_job is not None and isinstance(copywriter_job.progress, list):
                progress_events.extend([event for event in copywriter_job.progress if isinstance(event, dict)])

            if isinstance(job.progress, list):
                progress_events.extend([event for event in job.progress if isinstance(event, dict)])

            progress_events.sort(key=lambda event: str(event.get("ts", "")))

            for event in progress_events:
                yield _sse_line(event)

            if job.status in {JobStatus.done, JobStatus.error}:
                if job.status == JobStatus.done:
                    yield _sse_line({"type": "done", "status": "done", "done": True})
                else:
                    yield _sse_line(
                        {
                            "type": "error",
                            "status": "error",
                            "message": job.error or "Job failed",
                            "done": True,
                        }
                    )
                return

            # Phase 3: subscribe to Redis for live events.
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                ssl_cert_reqs=None,
            )
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(channel)

            while True:
                if await request.is_disconnected():
                    break

                message = await pubsub.get_message(ignore_subscribe_messages=False, timeout=1.0)
                if not message or message.get("type") != "message":
                    continue

                data = message.get("data")
                payload_text = data if isinstance(data, str) else json.dumps(data)
                yield f"data: {payload_text}\n\n"

                try:
                    event = json.loads(payload_text)
                except Exception:
                    logger.warning("Non-JSON SSE payload on %s", channel)
                    continue

                if _should_close_stream(event, job.agent_type):
                    break

        except Exception as exc:
            logger.exception("SSE stream failure for job_id=%s", job_id)
            yield _sse_line(
                {
                    "type": "error",
                    "message": f"SSE stream error: {str(exc)}",
                    "done": True,
                }
            )
            return
        finally:
            if pubsub is not None:
                try:
                    await pubsub.unsubscribe(channel)
                except Exception:
                    logger.exception("Failed to unsubscribe pubsub channel %s", channel)
                try:
                    close_pubsub = getattr(pubsub, "aclose", None)
                    if callable(close_pubsub):
                        await close_pubsub()
                    else:
                        await pubsub.close()
                except Exception:
                    logger.exception("Failed to close pubsub for %s", channel)

            if redis_client is not None:
                try:
                    await redis_client.aclose()
                except Exception:
                    logger.exception("Failed to close redis client for %s", channel)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
