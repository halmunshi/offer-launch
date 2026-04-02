from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    query,
)

from app.agents.context import (
    AGENTS_DIR,
    build_agent_context,
    build_component_manifest,
    build_session_context,
    list_funnel_file_paths,
    load_boilerplate_components,
)
from app.agents.hooks import build_hooks
from app.agents.state import AgentState
from app.agents.tools import (
    delete_funnel_file,
    edit_funnel_file,
    read_funnel_file,
    write_funnel_file,
)

FUNNEL_BUILDER_CWD: Path = AGENTS_DIR / "funnel_builder"
FUNNEL_BUILDER_SYSTEM_PROMPT_PATH = FUNNEL_BUILDER_CWD / "funnel_builder_system_prompt.md"
MODEL = "claude-haiku-4-5-20251001"
THINKING_BUDGET_TOKENS = 8000
# Claude Agent SDK/CLI currently exposes `thinking` but does not expose
# a `max_tokens` option for per-turn output caps. TODO: set max_tokens=16000
# when SDK/CLI surfaces that parameter.

def _load_system_prompt_template() -> str:
    if not FUNNEL_BUILDER_SYSTEM_PROMPT_PATH.exists():
        raise RuntimeError(f"Missing system prompt file: {FUNNEL_BUILDER_SYSTEM_PROMPT_PATH}")
    return FUNNEL_BUILDER_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _load_anthropic_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return ""

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not stripped.startswith("ANTHROPIC_API_KEY="):
                continue
            value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    except Exception:
        return ""

    return ""


def _normalize_selected_pages(selected_pages: object, funnel_type: str) -> list[str]:
    pages: list[str] = []
    seen: set[str] = set()

    if isinstance(selected_pages, list):
        for page in selected_pages:
            normalized = str(page).strip().lower().replace("-", "_").replace(" ", "_")
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            pages.append(normalized)

    if pages:
        return pages

    if funnel_type == "lead_magnet":
        return ["opt_in", "thank_you"]
    return ["vsl", "order", "thank_you"]


def _build_generation_instruction(
    selected_pages: list[str],
    funnel_type: str,
    theme_direction: str,
) -> str:
    page_list = "\n".join(f"  - {page}" for page in selected_pages)
    return f"""
=== BUILD INSTRUCTIONS ===
Funnel type: {funnel_type}
Theme direction: {theme_direction}
Pages to build (in this order):
{page_list}

Generation order - strictly follow this:
1. Write /src/theme.ts first (all pages import from it)
2. Load the relevant theme skill for {theme_direction}
3. Load the funnel-type skill for {funnel_type}
4. Write each page in the order listed above
5. Write /src/App.tsx last with routes for all pages

/src/pages/ is empty - create all selected pages from scratch.
Use the copy from the offer context for all visible text.
Do not write placeholder text.
"""


def _read_thinking_text(block) -> str:
    if isinstance(block, dict):
        if block.get("type") == "thinking":
            return str(block.get("thinking", ""))
        return ""

    if getattr(block, "type", None) == "thinking":
        return str(getattr(block, "thinking", ""))

    return ""


async def funnel_builder_node(state: AgentState) -> AgentState:
    """
    LangGraph node - funnel builder initial generation (Pattern A query()).

    /src/pages/ starts empty in boilerplate; agent creates all selected pages.
    Order:
      1) /src/theme.ts
      2) page files
      3) /src/App.tsx
    """
    from claude_agent_sdk import create_sdk_mcp_server, tool

    state["progress"].append(
        {
            "type": "start",
            "stage": "funnel_builder",
            "message": "Starting funnel generation",
            "ts": datetime.now(timezone.utc).isoformat(),
            "done": False,
        }
    )

    api_key = _load_anthropic_api_key()
    db = state.get("db") if isinstance(state, dict) else None

    @tool(
        "read_funnel_file",
        "Read the current content of a file from the funnel project",
        {"path": {"type": "string", "description": "File path e.g. /src/pages/VSL.tsx"}},
    )
    async def _read(args: dict) -> dict:
        path = args.get("path", "")
        content = await read_funnel_file(path=path, funnel_id=state["funnel_id"], db=db)
        return {"content": [{"type": "text", "text": content or ""}]}

    @tool(
        "write_funnel_file",
        "Write a complete file to the funnel project. Use for new files and full rewrites.",
        {
            "path": {"type": "string", "description": "File path e.g. /src/pages/VSL.tsx"},
            "content": {"type": "string", "description": "Full file content"},
        },
    )
    async def _write(args: dict) -> dict:
        path = args.get("path", "")
        content = args.get("content", "")
        await write_funnel_file(path=path, content=content, funnel_id=state["funnel_id"], db=db)

        return {"content": [{"type": "text", "text": f"Written: {path}"}]}

    @tool(
        "edit_funnel_file",
        "Make a surgical single-block edit. Read the file first to get exact old_str.",
        {
            "path": {"type": "string", "description": "File path"},
            "old_str": {"type": "string", "description": "Exact string to replace"},
            "new_str": {"type": "string", "description": "Replacement string"},
        },
    )
    async def _edit(args: dict) -> dict:
        path = args.get("path", "")
        old_str = args.get("old_str", "")
        new_str = args.get("new_str", "")
        result = await edit_funnel_file(
            path=path,
            old_str=old_str,
            new_str=new_str,
            funnel_id=state["funnel_id"],
            db=db,
        )
        return {"content": [{"type": "text", "text": result}]}

    @tool(
        "delete_funnel_file",
        "Remove a file from the funnel project. Always rewrite App.tsx after.",
        {"path": {"type": "string", "description": "File path to delete"}},
    )
    async def _delete(args: dict) -> dict:
        path = args.get("path", "")
        await delete_funnel_file(path=path, funnel_id=state["funnel_id"], db=db)

        return {"content": [{"type": "text", "text": f"Deleted: {path}"}]}

    tools_server = create_sdk_mcp_server(name="tools", tools=[_read, _write, _edit, _delete])

    system_prompt = _load_system_prompt_template().format(
        component_source=load_boilerplate_components(),
        component_manifest=build_component_manifest(),
    )

    intake = state.get("offer_intake") or {}
    selected_pages = _normalize_selected_pages(intake.get("selected_pages"), state.get("funnel_type", "vsl"))
    funnel_type = str(state.get("funnel_type", "vsl"))
    theme_direction = str(state.get("theme_direction", intake.get("theme", "direct-response")))

    agent_context = build_agent_context(agent_type="funnel_builder", intake=intake)
    copy_markdown = state.get("copywriter_output")
    copy_context = ""
    if isinstance(copy_markdown, str) and copy_markdown.strip():
        copy_context = "=== COPY TO USE ===\n" + copy_markdown.strip()

    page_instruction = _build_generation_instruction(
        selected_pages=selected_pages,
        funnel_type=funnel_type,
        theme_direction=theme_direction,
    )

    prompt_parts = [part for part in [agent_context, copy_context, page_instruction] if part]
    prompt = "\n\n".join(prompt_parts)

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=system_prompt,
        mcp_servers={"tools": tools_server},
        allowed_tools=[
            "mcp__tools__read_funnel_file",
            "mcp__tools__write_funnel_file",
            "mcp__tools__edit_funnel_file",
            "mcp__tools__delete_funnel_file",
            "Skill",
        ],
        setting_sources=["project"],
        cwd=str(FUNNEL_BUILDER_CWD),
        hooks=build_hooks(state),
        permission_mode="bypassPermissions",
        max_turns=30,
        thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET_TOKENS},
        env={"ANTHROPIC_API_KEY": api_key} if api_key else {},
    )

    result_text: Optional[str] = None

    state["progress"].append(
        {
            "type": "status",
            "stage": "funnel_builder",
            "message": "Agent configured, beginning generation turns",
            "ts": datetime.now(timezone.utc).isoformat(),
            "done": False,
        }
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in getattr(message, "content", []) or []:
                thinking = _read_thinking_text(block)
                if thinking:
                    state["progress"].append(
                        {
                            "type": "thinking",
                            "stage": "funnel_builder",
                            "content": thinking,
                            "ts": datetime.now(timezone.utc).isoformat(),
                        }
                    )
        elif isinstance(message, ResultMessage):
            if message.subtype == "success":
                result_text = message.result
            else:
                raise RuntimeError(f"funnel_builder agent failed: {message.subtype}")
            break

    if not result_text:
        raise RuntimeError("funnel_builder returned empty result. Celery will retry.")

    state["funnel_builder_output"] = {
        "status": "done",
        "result": result_text,
        "funnel_type": funnel_type,
        "pages": selected_pages,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    state["progress"].append(
        {
            "type": "done",
            "stage": "funnel_builder",
            "message": f"Funnel built: {', '.join(selected_pages)}",
            "ts": datetime.now(timezone.utc).isoformat(),
            "done": True,
        }
    )

    return state


async def run_interactive_session(
    funnel_id: str,
    user_id: str,
    user_message: str,
    db,
) -> tuple[ClaudeAgentOptions, Optional[str]]:
    """
    Interactive builder chat setup - Pattern B (ClaudeSDKClient).

    Returns options + session_context for router-owned client lifecycle.
    """
    from claude_agent_sdk import create_sdk_mcp_server, tool

    _ = (user_id, user_message)
    api_key = _load_anthropic_api_key()

    @tool("read_funnel_file", "Read current content", {"path": {"type": "string"}})
    async def _read(args: dict) -> dict:
        path = args.get("path", "")
        content = await read_funnel_file(path, funnel_id, db)
        return {"content": [{"type": "text", "text": content or ""}]}

    @tool(
        "write_funnel_file",
        "Write complete file",
        {"path": {"type": "string"}, "content": {"type": "string"}},
    )
    async def _write(args: dict) -> dict:
        path = args.get("path", "")
        content = args.get("content", "")
        await write_funnel_file(path, content, funnel_id, db)
        return {"content": [{"type": "text", "text": f"Written: {path}"}]}

    @tool(
        "edit_funnel_file",
        "Surgical single-block edit",
        {
            "path": {"type": "string"},
            "old_str": {"type": "string"},
            "new_str": {"type": "string"},
        },
    )
    async def _edit(args: dict) -> dict:
        path = args.get("path", "")
        old_str = args.get("old_str", "")
        new_str = args.get("new_str", "")
        result = await edit_funnel_file(path, old_str, new_str, funnel_id, db)
        return {"content": [{"type": "text", "text": result}]}

    @tool("delete_funnel_file", "Delete file", {"path": {"type": "string"}})
    async def _delete(args: dict) -> dict:
        path = args.get("path", "")
        await delete_funnel_file(path, funnel_id, db)
        return {"content": [{"type": "text", "text": f"Deleted: {path}"}]}

    tools_server = create_sdk_mcp_server(name="tools", tools=[_read, _write, _edit, _delete])

    interactive_state = {
        "funnel_id": funnel_id,
        "job_id": "",
        "offer_intake": None,
        "progress": [],
    }

    system_prompt = _load_system_prompt_template().format(
        component_source=load_boilerplate_components(),
        component_manifest=build_component_manifest(),
    )

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=system_prompt,
        mcp_servers={"tools": tools_server},
        allowed_tools=[
            "mcp__tools__read_funnel_file",
            "mcp__tools__write_funnel_file",
            "mcp__tools__edit_funnel_file",
            "mcp__tools__delete_funnel_file",
            "Skill",
        ],
        setting_sources=["project"],
        cwd=str(FUNNEL_BUILDER_CWD),
        hooks=build_hooks(interactive_state),
        permission_mode="bypassPermissions",
        max_turns=20,
        thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET_TOKENS},
        env={"ANTHROPIC_API_KEY": api_key} if api_key else {},
    )

    project = await _get_funnel_project(funnel_id, db)
    recent_messages = await _get_recent_chat_messages(funnel_id, limit=20, db=db)
    file_paths = list_funnel_file_paths(getattr(project, "files", {}) if project else {})

    session_context = build_session_context(
        session_summary=getattr(project, "session_summary", None) if project else None,
        recent_messages=recent_messages,
        all_messages=[],
        file_paths=file_paths,
    )

    if isinstance(session_context, list):
        # Interactive setup path expects a compact setup string or None.
        session_context = None

    return options, session_context


async def _get_funnel_project(funnel_id: str, db):
    """
    TODO Phase 4: SELECT project by funnel_id with files + session_summary.
    """
    _ = (funnel_id, db)
    return None


async def _get_recent_chat_messages(
    funnel_id: str,
    limit: int = 20,
    db=None,
) -> list[dict]:
    """
    TODO Phase 4: SELECT recent chat_messages and map to {role, content, metadata}.
    """
    _ = (funnel_id, limit, db)
    return []
