from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Optional
import re

from anthropic import Anthropic
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, query

from app.agents.context import AGENTS_DIR, build_agent_context
from app.agents.hooks import emit_progress_event
from app.agents.state import AgentState

ANTHROPIC_CLIENT = Anthropic()
MODEL = "claude-haiku-4-5-20251001"
COPYWRITER_CWD: Path = AGENTS_DIR / "copywriter"
COPYWRITER_SYSTEM_PROMPT_PATH = COPYWRITER_CWD / "copywriter_system_prompt.md"

def _load_system_prompt() -> str:
    if not COPYWRITER_SYSTEM_PROMPT_PATH.exists():
        raise RuntimeError(f"Missing system prompt file: {COPYWRITER_SYSTEM_PROMPT_PATH}")
    return COPYWRITER_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _load_anthropic_api_key() -> str:
    """
    Load Anthropic API key from environment, with .env fallback for local runs.
    """
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


async def _append_progress(state: AgentState, event: dict) -> None:
    """
    Appends, persists, and streams a copywriter progress event.
    """
    await emit_progress_event(state, event, publish_sse=True)


def _extract_page_headings(markdown: str) -> list[str]:
    """
    Extract ## headings from copywriter markdown output.
    """
    headings: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            headings.append(stripped[3:].strip())
    return headings


def _is_sdk_runtime_error_text(text: str) -> bool:
    lowered = text.strip().lower()
    error_markers = [
        "not logged in",
        "credit balance is too low",
        "authentication",
        "billing",
        "rate limit",
    ]
    return any(marker in lowered for marker in error_markers)


def _normalize_page_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


PAGE_ALIASES: dict[str, tuple[str, ...]] = {
    "presell": ("presell", "pre sell"),
    "vsl": ("vsl", "video sales letter"),
    "landing": ("landing", "landing page", "sales page"),
    "booking": ("booking", "book", "book call", "schedule"),
    "confirmation": ("confirmation", "confirmed", "success", "booked"),
    "order": ("order",),
    "thank_you": ("thankyou", "thank you"),
    "upsell": ("upsell",),
    "downsell": ("downsell",),
    "opt_in": ("optin", "opt in", "squeeze"),
    "bridge": ("bridge",),
    "offer": ("offer",),
}


def _get_selected_pages(selected_pages: object, funnel_type: str) -> list[str]:
    if not isinstance(selected_pages, list):
        selected_pages = []

    selected: list[str] = []
    seen: set[str] = set()
    for page in selected_pages:
        normalized = str(page).strip().lower().replace("-", "_").replace(" ", "_")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        selected.append(normalized)

    if not selected:
        normalized_type = str(funnel_type).strip().lower()
        if normalized_type == "lead_generation":
            return ["opt_in", "thank_you"]
        if normalized_type == "call_funnel":
            return ["landing", "booking", "confirmation"]
        if normalized_type == "direct_sales":
            return ["landing", "order", "thank_you"]
        return ["landing", "order", "thank_you"]

    return selected


def _build_page_scope_instruction(funnel_type: str, selected_pages: list[str]) -> str:
    selected_list = ", ".join(selected_pages) if selected_pages else "none"

    return "\n".join(
        [
            "=== PAGE SELECTION CONSTRAINT ===",
            f"Funnel type: {funnel_type}",
            f"Selected pages: {selected_list}",
            "Write copy for exactly the selected pages only.",
            "Do not include any page section that is not in selected_pages.",
            "Use one ## section heading per selected page.",
        ]
    )


def _validate_selected_pages(markdown: str, selected_pages: list[str]) -> None:
    selected = set(selected_pages)

    headings = _extract_page_headings(markdown)
    normalized_headings = [_normalize_page_key(heading) for heading in headings]

    found_pages: set[str] = set()
    for page_key, aliases in PAGE_ALIASES.items():
        for heading in normalized_headings:
            normalized_aliases = [_normalize_page_key(alias) for alias in aliases]
            if any(alias in heading for alias in normalized_aliases):
                found_pages.add(page_key)
                break

    unexpected = sorted(found_pages - selected)
    if unexpected:
        raise RuntimeError(
            "Copywriter wrote unselected pages: "
            f"{', '.join(unexpected)}. Celery will retry."
        )

    missing = sorted(selected - found_pages)
    if missing:
        raise RuntimeError(
            "Copywriter missed selected pages: "
            f"{', '.join(missing)}. Celery will retry."
        )


async def copywriter_node(state: AgentState) -> AgentState:
    """
    LangGraph node for one-shot copy generation using the Claude Agent SDK.
    """
    context = build_agent_context(
        agent_type="copywriter",
        intake=state.get("offer_intake"),
        offer_industry=state.get("offer_industry"),
        funnel_name=state.get("funnel_name"),
        funnel_type=state.get("funnel_type"),
        funnel_style=state.get("funnel_style"),
        funnel_integrations=state.get("funnel_integrations"),
    )
    if not context:
        state["copywriter_output"] = None
        await _append_progress(
            state,
            {
                "stage": "copywriter",
                "message": "Skipped - no offer context provided",
                "ts": datetime.now(timezone.utc).isoformat(),
                "done": True,
            }
        )
        return state

    funnel_type = str(state.get("funnel_type") or "unknown")
    selected_pages = _get_selected_pages(state.get("selected_pages"), funnel_type)
    context = f"{context}\n\n{_build_page_scope_instruction(funnel_type, selected_pages)}"

    api_key = _load_anthropic_api_key()

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=_load_system_prompt(),
        allowed_tools=["Skill"],
        setting_sources=["project"],
        cwd=str(COPYWRITER_CWD),
        max_turns=5,
        env={"ANTHROPIC_API_KEY": api_key} if api_key else {},
    )

    markdown_output: Optional[str] = None

    async for message in query(prompt=context, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                thinking_text = getattr(block, "thinking", "")
                if thinking_text:
                    await _append_progress(
                        state,
                        {
                            "type": "thinking",
                            "content": thinking_text,
                            "stage": "copywriter",
                            "ts": datetime.now(timezone.utc).isoformat(),
                        },
                    )
        elif isinstance(message, ResultMessage):
            if message.subtype == "success":
                markdown_output = message.result or ""
            else:
                raise RuntimeError(f"Copywriter agent failed: {message.subtype}")
            break

    if not markdown_output or not markdown_output.strip():
        raise RuntimeError("Copywriter returned empty output. Celery will retry.")

    if _is_sdk_runtime_error_text(markdown_output):
        raise RuntimeError(f"Copywriter runtime error from SDK: {markdown_output.strip()}")

    if "##" not in markdown_output:
        raise RuntimeError(
            "Copywriter output missing page headings. Expected Markdown with ## sections. Celery will retry."
        )

    _validate_selected_pages(markdown_output, selected_pages)

    pages_written = _extract_page_headings(markdown_output)

    state["copywriter_output"] = markdown_output

    await _append_progress(
        state,
        {
            "stage": "copywriter",
            "message": f"Copy written for {len(pages_written)} pages: {', '.join(pages_written)}",
            "ts": datetime.now(timezone.utc).isoformat(),
            "done": True,
            "type": "done",
        }
    )

    return state
