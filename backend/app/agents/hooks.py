from datetime import datetime, timezone
import json
import logging
from typing import Optional
from uuid import uuid4

import redis.asyncio as aioredis
from sqlalchemy import text

from app.agents.state import AgentState

logger = logging.getLogger(__name__)

try:
    from app.config import settings

    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        ssl_cert_reqs=None,
    )
except Exception:
    redis_client = None


def _get_async_session_local():
    try:
        from app.database import AsyncSessionLocal

        return AsyncSessionLocal
    except Exception:
        logger.exception("Database session factory unavailable in hooks")
        return None


async def _insert_chat_message(
    funnel_id: str, role: str, content: str, metadata: Optional[dict] = None
) -> None:
    if not funnel_id or not role:
        return

    try:
        session_factory = _get_async_session_local()
        if session_factory is None:
            return

        async with session_factory() as db:
            user_result = await db.execute(
                text(
                    """
                    SELECT user_id
                    FROM funnel_projects
                    WHERE funnel_id = CAST(:funnel_id AS uuid)
                    """
                ),
                {"funnel_id": funnel_id},
            )
            user_id = user_result.scalar_one_or_none()
            if user_id is None:
                logger.warning("Skipping chat_messages insert; no funnel_project user for funnel_id=%s", funnel_id)
                return

            await db.execute(
                text(
                    """
                    INSERT INTO chat_messages (
                        id,
                        funnel_id,
                        user_id,
                        role,
                        content,
                        metadata,
                        created_at
                    )
                    VALUES (
                        CAST(:id AS uuid),
                        CAST(:funnel_id AS uuid),
                        CAST(:user_id AS uuid),
                        :role,
                        :content,
                        CAST(:metadata AS jsonb),
                        now()
                    )
                    """
                ),
                {
                    "id": str(uuid4()),
                    "funnel_id": funnel_id,
                    "user_id": str(user_id),
                    "role": role,
                    "content": content,
                    "metadata": json.dumps(metadata),
                },
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to insert chat message for funnel_id=%s", funnel_id)


async def insert_chat_message(
    funnel_id: str, role: str, content: str, metadata: Optional[dict] = None
) -> None:
    await _insert_chat_message(
        funnel_id=funnel_id,
        role=role,
        content=content,
        metadata=metadata,
    )


def _resolve_progress_job_id(state: AgentState, event: dict) -> str | None:
    stage = str(event.get("stage", "")).strip()

    if stage == "copywriter":
        copywriter_job_id = state.get("copywriter_job_id")
        if isinstance(copywriter_job_id, str) and copywriter_job_id.strip():
            return copywriter_job_id
        return None

    if stage == "funnel_builder":
        funnel_builder_job_id = state.get("job_id")
        if isinstance(funnel_builder_job_id, str) and funnel_builder_job_id.strip():
            return funnel_builder_job_id
        return None

    return None


async def _append_job_progress(state: AgentState, event: dict) -> None:
    job_id = _resolve_progress_job_id(state, event)
    if not job_id:
        return

    try:
        session_factory = _get_async_session_local()
        if session_factory is None:
            return

        async with session_factory() as db:
            await db.execute(
                text(
                    """
                    UPDATE jobs
                    SET progress = progress || CAST(:event AS jsonb),
                        updated_at = now()
                    WHERE id = CAST(:job_id AS uuid)
                    """
                ),
                {
                    "job_id": job_id,
                    "event": json.dumps(event),
                },
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to append progress for job_id=%s", job_id)


async def _append_sse_event(job_id: str, event: dict) -> None:
    if not job_id or redis_client is None:
        return

    try:
        await redis_client.publish(f"job:{job_id}", json.dumps(event))
    except Exception:
        logger.exception("Failed to publish SSE event for job_id=%s", job_id)


async def emit_progress_event(state: AgentState, event: dict, publish_sse: bool = True) -> None:
    """
    Unified progress emitter used by agent nodes.

    - Always appends to in-memory state progress.
    - Persists to the correct job row based on event stage.
    - Publishes to the funnel_builder SSE channel when requested.
    """
    _append_local_progress(state, event)
    await _append_job_progress(state, event)

    if not publish_sse:
        return

    stream_job_id = state.get("job_id")
    if isinstance(stream_job_id, str) and stream_job_id.strip():
        await _append_sse_event(stream_job_id, event)


async def _update_session_summary(funnel_id: str, summary: str) -> None:
    if not funnel_id:
        return

    try:
        session_factory = _get_async_session_local()
        if session_factory is None:
            return

        async with session_factory() as db:
            await db.execute(
                text(
                    """
                    UPDATE funnel_projects
                    SET session_summary = :summary,
                        updated_at = now()
                    WHERE funnel_id = CAST(:funnel_id AS uuid)
                    """
                ),
                {
                    "summary": summary,
                    "funnel_id": funnel_id,
                },
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to update session summary for funnel_id=%s", funnel_id)


def _hook_get(hook_input, key: str, default=None):
    if isinstance(hook_input, dict):
        return hook_input.get(key, default)
    return getattr(hook_input, key, default)


def _append_local_progress(state: AgentState, event: dict) -> None:
    """
    Phase 3 fallback: append hook events directly to in-memory state progress.
    Phase 4 will additionally persist via jobs.progress + SSE.
    """
    progress = state.get("progress")
    if isinstance(progress, list):
        progress.append(event)


def build_hooks(state: AgentState) -> dict:
    """
    Hook factory for funnel_builder agent.

    PreCompact note:
    Haiku 4.5 does not support automatic SDK compaction, so PreCompact
    is wired but will not fire in MVP. Manual compaction is handled in
    session context reconstruction logic.
    """

    funnel_id_value = state.get("funnel_id")
    funnel_id = funnel_id_value if isinstance(funnel_id_value, str) else ""

    job_id_value = state.get("job_id")
    job_id = job_id_value if isinstance(job_id_value, str) else ""

    async def pre_tool_use_hook(hook_input, tool_use_id, context):
        _ = (tool_use_id, context)
        tool_name = _hook_get(hook_input, "tool_name", "") or ""
        if "write_funnel_file" not in tool_name:
            return {}

        tool_input = _hook_get(hook_input, "tool_input", {}) or {}
        path = tool_input.get("path", "")

        if funnel_id:
            await _insert_chat_message(
                funnel_id=funnel_id,
                role="tool_call",
                content="write_funnel_file",
                metadata={"tool_name": "write_funnel_file", "path": path},
            )

        if job_id:
            await _append_job_progress(
                state,
                {
                    "type": "tool_call",
                    "stage": "funnel_builder",
                    "message": f"write_funnel_file -> {path}",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "done": False,
                },
            )
            await _append_sse_event(
                job_id,
                {
                    "type": "tool_call",
                    "tool": "write_funnel_file",
                    "path": path,
                },
            )

        _append_local_progress(
            state,
            {
                "type": "tool_call",
                "stage": "funnel_builder",
                "message": f"write_funnel_file -> {path}",
                "ts": datetime.now(timezone.utc).isoformat(),
                "done": False,
            },
        )

        return {}

    async def post_tool_use_hook(hook_input, tool_use_id, context):
        _ = (tool_use_id, context)
        tool_name = _hook_get(hook_input, "tool_name", "") or ""
        tool_input = _hook_get(hook_input, "tool_input", {}) or {}

        if "read_funnel_file" in tool_name:
            return {}

        path = tool_input.get("path", "")
        content = tool_input.get("content", "")

        if funnel_id:
            await _insert_chat_message(
                funnel_id=funnel_id,
                role="tool_result",
                content=f"Updated: {path}",
                metadata={"path": path, "status": "updated"},
            )

        if job_id:
            await _append_job_progress(
                state,
                {
                    "type": "file_update",
                    "stage": "funnel_builder",
                    "message": f"Updated: {path}",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "done": False,
                },
            )
            await _append_sse_event(
                job_id,
                {
                    "type": "file_update",
                    "path": path,
                    "content": content,
                },
            )

        _append_local_progress(
            state,
            {
                "type": "file_update",
                "stage": "funnel_builder",
                "message": f"Updated: {path}",
                "ts": datetime.now(timezone.utc).isoformat(),
                "done": False,
            },
        )

        return {}

    async def pre_compact_hook(hook_input, tool_use_id, context):
        _ = (tool_use_id, context)
        summary = _hook_get(hook_input, "summary", "") or _hook_get(hook_input, "compact_summary", "")
        if funnel_id and isinstance(summary, str) and summary.strip():
            await _update_session_summary(funnel_id=funnel_id, summary=summary.strip())
        # Haiku 4.5: no automatic compaction trigger in MVP.
        # Kept here for forward compatibility with Sonnet 4.6+.
        return {}

    async def stop_hook(hook_input, tool_use_id, context):
        _ = (hook_input, tool_use_id, context)
        if job_id:
            await _append_job_progress(
                state,
                {
                    "type": "done",
                    "stage": "funnel_builder",
                    "message": "Generation complete",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "done": True,
                },
            )
        _append_local_progress(
            state,
            {
                "type": "done",
                "stage": "funnel_builder",
                "message": "Generation complete",
                "ts": datetime.now(timezone.utc).isoformat(),
                "done": True,
            },
        )
        return {}

    return {
        "PreCompact": [
            {"hooks": [pre_compact_hook]},
        ],
    }
