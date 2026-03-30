from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Optional
import re

from anthropic import Anthropic
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, query

from app.agents.context import AGENTS_DIR, build_agent_context
from app.agents.state import AgentState

ANTHROPIC_CLIENT = Anthropic()
MODEL = "claude-haiku-4-5-20251001"
COPYWRITER_CWD: Path = AGENTS_DIR / "copywriter"

COPYWRITER_SYSTEM_PROMPT = """
You are a world-class direct response copywriter working for OfferLaunch.
You write conversion-focused copy for any industry, any audience, any offer.
You never assume a vertical. You write from the offer context given to you.

## Your task
Write complete funnel copy for every page the user has selected.
Before writing, load the skill file for the funnel type using the Skill tool.
The skill tells you which pages exist, what each page needs, and which
copywriting frameworks to apply per page.

## Output format
- Output ONLY a Markdown document
- Use ## headings for each page section (e.g. ## VSL Page, ## Order Page)
- Within each section, write the actual copy - headlines, subheadlines,
  body copy, bullet points, CTAs - in natural Markdown
- No preamble. No explanation. No meta-commentary. No JSON. No code blocks.
- Start writing immediately after the skill is loaded.

## Copy quality
- Every word must be real, usable copy - never placeholder text
- Specificity beats vagueness every time
- Benefits over features always
- Match the copy_style from the offer context exactly
- The transformation field is your North Star - every page points to it
- Write for the exact audience described - age, pain point, awareness level
- One CTA per page - never more

## Framework
The skill file contains the Brunson framework for each page type.
Apply it - but serve the reader, not the framework.
Great copy follows the reader's psychology, not a rigid template.
"""


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


def _append_progress(state: AgentState, event: dict) -> None:
    """
    Appends a progress event to state["progress"].
    """
    state["progress"].append(event)


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


def _build_page_scope_instruction(intake: dict) -> str:
    funnel_type = str(intake.get("funnel_type", "")).strip() or "unknown"
    optional_pages = intake.get("optional_pages")
    if not isinstance(optional_pages, list):
        optional_pages = []

    selected = [str(page).strip() for page in optional_pages if str(page).strip()]
    selected_list = ", ".join(selected) if selected else "none"

    return "\n".join(
        [
            "=== PAGE SELECTION CONSTRAINT ===",
            f"Funnel type: {funnel_type}",
            f"Selected optional pages: {selected_list}",
            "Write copy for core pages of this funnel type plus selected optional pages only.",
            "If selected optional pages are none, do not include any optional page sections.",
            "Do not add unselected optional pages.",
        ]
    )


def _validate_optional_pages(markdown: str, intake: dict) -> None:
    optional_pages = intake.get("optional_pages")
    if not isinstance(optional_pages, list):
        optional_pages = []

    selected = {_normalize_page_key(str(page)) for page in optional_pages if str(page).strip()}

    optional_aliases = {
        "upsell": ("upsell",),
        "downsell": ("downsell",),
        "bridge": ("bridge",),
        "offer": ("offer",),
    }

    headings = _extract_page_headings(markdown)
    normalized_headings = [_normalize_page_key(heading) for heading in headings]

    found_optional: set[str] = set()
    for optional_key, aliases in optional_aliases.items():
        for heading in normalized_headings:
            if any(alias in heading for alias in aliases):
                found_optional.add(optional_key)
                break

    unexpected = sorted(found_optional - selected)
    if unexpected:
        raise RuntimeError(
            "Copywriter wrote unselected optional pages: "
            f"{', '.join(unexpected)}. Celery will retry."
        )

    missing = sorted(selected - found_optional)
    if missing:
        raise RuntimeError(
            "Copywriter missed selected optional pages: "
            f"{', '.join(missing)}. Celery will retry."
        )


async def copywriter_node(state: AgentState) -> AgentState:
    """
    LangGraph node for one-shot copy generation using the Claude Agent SDK.
    """
    context = build_agent_context(
        agent_type="copywriter",
        intake=state.get("offer_intake"),
    )
    if not context:
        state["copywriter_output"] = None
        state["progress"].append(
            {
                "stage": "copywriter",
                "message": "Skipped - no offer context provided",
                "ts": datetime.now(timezone.utc).isoformat(),
                "done": True,
            }
        )
        return state

    intake = state.get("offer_intake") or {}
    context = f"{context}\n\n{_build_page_scope_instruction(intake)}"

    api_key = _load_anthropic_api_key()

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=COPYWRITER_SYSTEM_PROMPT,
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
                    _append_progress(
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

    _validate_optional_pages(markdown_output, intake)

    pages_written = _extract_page_headings(markdown_output)

    state["copywriter_output"] = {
        "markdown": markdown_output,
        "path": "/src/content.md",
        "pages_written": pages_written,
        "funnel_type": state.get("funnel_type", "unknown"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    state["progress"].append(
        {
            "stage": "copywriter",
            "message": f"Copy written for {len(pages_written)} pages: {', '.join(pages_written)}",
            "ts": datetime.now(timezone.utc).isoformat(),
            "done": True,
            "type": "done",
        }
    )

    return state
