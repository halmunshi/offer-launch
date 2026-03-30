from datetime import datetime, timezone
from typing import Optional

from app.agents.state import AgentState


async def _insert_chat_message(
    funnel_id: str, role: str, content: str, metadata: Optional[dict] = None
) -> None:
    """
    TODO Phase 4: INSERT INTO chat_messages (funnel_id, role, content, metadata).
    Stores tool_call, tool_result, and agent messages for UI rendering.
    """
    _ = (funnel_id, role, content, metadata)


async def _append_job_progress(job_id: str, event: dict) -> None:
    """
    TODO Phase 4: UPDATE jobs SET progress = progress || $event WHERE id = $job_id.
    Append-only. Never overwrite.
    """
    _ = (job_id, event)


async def _append_sse_event(job_id: str, event: dict) -> None:
    """
    TODO Phase 4: Publish SSE event to Redis pub/sub for job_id channel.
    """
    _ = (job_id, event)


async def _update_session_summary(funnel_id: str, summary: str) -> None:
    """
    TODO Phase 4: UPDATE funnel_projects SET session_summary = $summary.
    Called by PreCompact hook when context compaction is supported.
    """
    _ = (funnel_id, summary)


def _hook_get(hook_input, key: str, default=None):
    if isinstance(hook_input, dict):
        return hook_input.get(key, default)
    return getattr(hook_input, key, default)


def build_hooks(state: AgentState) -> dict:
    """
    Hook factory for funnel_builder agent.

    PreCompact note:
    Haiku 4.5 does not support automatic SDK compaction, so PreCompact
    is wired but will not fire in MVP. Manual compaction is handled in
    session context reconstruction logic.
    """

    funnel_id = str(state.get("funnel_id", ""))
    job_id = str(state.get("job_id", ""))

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
            await _append_sse_event(
                job_id,
                {
                    "type": "tool_call",
                    "tool": "write_funnel_file",
                    "path": path,
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
                job_id,
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

        return {}

    async def pre_compact_hook(hook_input, tool_use_id, context):
        _ = (hook_input, tool_use_id, context)
        # Haiku 4.5: no automatic compaction trigger in MVP.
        # Kept here for forward compatibility with Sonnet 4.6+.
        return {}

    async def stop_hook(hook_input, tool_use_id, context):
        _ = (hook_input, tool_use_id, context)
        if job_id:
            await _append_job_progress(
                job_id,
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
        "PreToolUse": [
            {"matcher": "mcp__tools__write_funnel_file", "hooks": [pre_tool_use_hook]},
        ],
        "PostToolUse": [
            {"hooks": [post_tool_use_hook]},
        ],
        "PreCompact": [
            {"hooks": [pre_compact_hook]},
        ],
        "Stop": [
            {"hooks": [stop_hook]},
        ],
    }
