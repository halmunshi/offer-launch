import json
import re
from pathlib import Path
from typing import Optional

import anthropic

ANTHROPIC_CLIENT = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
AGENTS_DIR = Path(__file__).resolve().parent


def _resolve_boilerplate_dir() -> Path:
    backend_root = AGENTS_DIR.parents[1]
    repo_root = AGENTS_DIR.parents[2]
    candidates = [
        backend_root / "boilerplate",
        repo_root / "boilerplate",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


BOILERPLATE_DIR = _resolve_boilerplate_dir()

CONTEXT_WINDOW = 200_000
SAFETY_BUFFER = 30_000
HISTORY_BUDGET = 150_000


def build_agent_context(
    agent_type: str,
    intake: Optional[dict] = None,
    offer_industry: Optional[str] = None,
    funnel_name: Optional[str] = None,
    funnel_type: Optional[str] = None,
    funnel_style: Optional[str] = None,
    funnel_integrations: Optional[dict] = None,
    copywriter_output: Optional[str] = None,
    analyst_output: Optional[dict] = None,
    session_summary: Optional[str] = None,
) -> Optional[str]:
    """
    Universal context assembler for any agent type, current or future.
    Returns None if there is nothing meaningful to inject.
    """

    def safe(val: object, max_len: int = 2000) -> str:
        if val is None:
            return ""
        text = str(val).strip()
        return text[:max_len] if text else ""

    known_agents = {
        "copywriter",
        "funnel_builder",
        "analyst",
        "media_buyer",
        "email_agent",
    }
    include_all = agent_type not in known_agents

    include_intake = include_all or agent_type in {
        "copywriter",
        "funnel_builder",
        "analyst",
        "media_buyer",
        "email_agent",
    }
    include_copywriter_output = include_all or agent_type in {"funnel_builder", "email_agent"}
    include_analyst_output = include_all or agent_type == "media_buyer"
    include_session_summary = include_all or agent_type in {"copywriter", "funnel_builder"}

    parts: list[str] = []

    if intake and include_intake:
        parts.append("=== OFFER CONTEXT ===")
        fields = [
            ("Offer name", intake.get("offer_name")),
            ("One-liner", intake.get("offer_one_liner")),
            ("Brand name", intake.get("brand_name")),
            ("Industry", offer_industry),
            ("Price point", intake.get("price_point")),
            ("Whats included", intake.get("whats_included")),
            ("Transformation", intake.get("transformation")),
        ]
        for label, val in fields:
            if val:
                parts.append(f"{label}: {safe(val)}")

        parts.append("\n=== AUDIENCE ===")
        for label, val in [
            ("Ideal client", intake.get("ideal_client")),
            ("Pain point", intake.get("pain_point")),
        ]:
            if val:
                parts.append(f"{label}: {safe(val)}")

    if include_intake and (funnel_name or funnel_type or funnel_style or funnel_integrations):
        parts.append("\n=== FUNNEL SETUP ===")
        for label, val in [
            ("Funnel name", funnel_name),
            ("Funnel type", funnel_type),
            ("Funnel style", funnel_style),
        ]:
            if val:
                parts.append(f"{label}: {safe(val)}")

        if funnel_integrations:
            integration_map = [
                ("Lead magnet type", funnel_integrations.get("lead_magnet_type")),
                ("Lead magnet description", funnel_integrations.get("lead_magnet_description")),
                ("Lead magnet ready", funnel_integrations.get("lead_magnet_ready")),
                ("Has VSL", funnel_integrations.get("has_vsl")),
                ("VSL embed", funnel_integrations.get("vsl_embed")),
                ("Calendar provider", funnel_integrations.get("calendar_provider")),
                ("Calendar embed", funnel_integrations.get("calendar_embed")),
                ("Payment processor", funnel_integrations.get("payment_processor")),
                ("Payment embed", funnel_integrations.get("payment_embed")),
                ("Selected pages", funnel_integrations.get("selected_pages")),
            ]
            for label, val in integration_map:
                if val is None or val == "" or val == []:
                    continue
                parts.append(f"{label}: {safe(val)}")

    if copywriter_output and include_copywriter_output:
        parts.append("\n=== COPY TO USE ===")
        parts.append(copywriter_output[:12000])

    if analyst_output and include_analyst_output:
        parts.append("\n=== MARKET ANALYSIS ===")
        parts.append(json.dumps(analyst_output, indent=2)[:8000])

    if session_summary and session_summary.strip() and include_session_summary:
        parts.append("\n=== SESSION CONTEXT ===")
        parts.append(session_summary.strip())

    if not parts:
        return None

    return "\n".join(parts)


def count_tokens(
    messages: list[dict],
    system: Optional[str] = None,
    tools: Optional[list] = None,
) -> int:
    """
    Calls Anthropic's token counting API and returns exact input token count.
    """
    kwargs: dict = {
        "model": MODEL,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools

    response = ANTHROPIC_CLIENT.messages.count_tokens(**kwargs)
    return response.input_tokens


def build_session_context(
    session_summary: Optional[str],
    recent_messages: list[dict],
    all_messages: list[dict],
    file_paths: list[str],
    system_prompt: Optional[str] = None,
    tools: Optional[list] = None,
) -> Optional[str] | list[dict]:
    """
    Chooses session resume context path:
    1) None for first session
    2) Full replay when under budget
    3) Summary + recent tail + generated file state
    """
    has_summary = bool(session_summary and session_summary.strip())
    has_messages = bool(all_messages)
    has_files = bool(file_paths)

    if not has_summary and not has_messages and not has_files:
        return None

    if has_messages:
        token_count = count_tokens(messages=all_messages, system=system_prompt, tools=tools)
        if token_count <= HISTORY_BUDGET:
            return all_messages

    parts: list[str] = []

    if has_summary:
        parts.append("=== PREVIOUS SESSION ===")
        parts.append(session_summary.strip())

    if recent_messages:
        parts.append("\n=== RECENT MESSAGES ===")
        for msg in recent_messages[-20:]:
            role = str(msg.get("role", "unknown")).upper()
            content = str(msg.get("content", ""))[:400]
            metadata = msg.get("metadata") or {}
            if role == "TOOL_CALL":
                path = metadata.get("path", "")
                tool_name = metadata.get("tool_name", "tool")
                parts.append(f"TOOL: {tool_name} -> {path}" if path else f"TOOL: {tool_name}")
            elif role == "TOOL_RESULT":
                path = metadata.get("path", "")
                status = metadata.get("status", "done")
                parts.append(f"RESULT: OK {path} ({status})" if path else f"RESULT: {status}")
            else:
                parts.append(f"{role}: {content}")

    if has_files:
        parts.append("\n=== CURRENT FILES ===")
        generated = sorted(
            [
                path
                for path in file_paths
                if not path.startswith("/src/components/")
                and not path.startswith("/src/lib/")
                and path
                not in {
                    "/index.html",
                    "/package.json",
                    "/vite.config.ts",
                    "/tsconfig.json",
                    "/tsconfig.app.json",
                    "/tsconfig.node.json",
                    "/components.json",
                    "/src/main.tsx",
                    "/src/index.css",
                    "/src/App.css",
                    "/README.md",
                }
            ]
        )
        if generated:
            parts.append("\n".join(generated))

    if not parts:
        return None

    return "\n".join(parts)


def build_component_manifest() -> str:
    """
    Builds a concise inventory from the actual boilerplate component directories.
    """
    boilerplate_dir = BOILERPLATE_DIR
    ui_dir = boilerplate_dir / "src" / "components" / "ui"
    funnel_dir = boilerplate_dir / "src" / "components" / "funnel"

    def list_components(directory: Path) -> list[str]:
        if not directory.exists():
            return []
        return sorted(
            [
                file_path.stem
                for file_path in directory.glob("*.tsx")
                if not file_path.name.startswith("_")
            ]
        )

    ui_components = list_components(ui_dir)
    funnel_components = list_components(funnel_dir)

    def to_kebab(name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()

    lines = [
        "=== AVAILABLE COMPONENTS ===",
        "",
        "-- UI components (shadcn + Magic UI - all in @/components/ui/) --",
        "   Both shadcn and Magic UI components install to the same ui/ directory.",
        "   Import all of them from @/components/ui/{kebab-name}",
    ]

    for name in ui_components:
        lines.append(f"  {name} -> import from @/components/ui/{to_kebab(name)}")

    lines.append("  See shadcn/ui and Magic UI docs for full props per component.")

    lines += [
        "",
        "-- Funnel-specific (import from @/components/funnel/{name}) --",
    ]

    if "VideoEmbed" in funnel_components:
        lines += [
            "  VideoEmbed",
            "    props: { url: string, placeholder?: string }",
            "    Handles YouTube, Vimeo, Wistia, Loom. Empty url shows placeholder.",
            "",
        ]

    if "CountdownTimer" in funnel_components:
        lines += [
            "  CountdownTimer",
            "    props: { targetDate?: string, minutes?: number,",
            "             label?: string, onExpire?: () => void }",
            "    Pass minutes for session timer, targetDate for fixed deadline.",
            "",
        ]

    lines += [
        "-- Utilities --",
        "  @/lib/utils -> { cn } for merging Tailwind class names",
        "",
        "-- Other imports --",
        "  lucide-react     -> icons (Check, Play, Shield, ChevronDown, etc.)",
        "  framer-motion    -> animations (motion.div, AnimatePresence, etc.)",
        "  react-router-dom -> { Link, useNavigate } for navigation",
        "",
        "=== RULES ===",
        "- Import ONLY from the paths listed above",
        "- Never hardcode colours - Tailwind classes only",
        "- Use read_funnel_file before editing any existing file",
        "- Every page component must have a default export",
        "- App.tsx must be rewritten when routes change",
    ]

    return "\n".join(lines)


def list_funnel_file_paths(files_jsonb: dict) -> list[str]:
    """
    Extract and sort file paths from funnel_projects.files JSONB.
    """
    if not files_jsonb:
        return []
    return sorted(
        [
            path
            for path in files_jsonb.keys()
            if not path.startswith("/node_modules/") and not path.startswith("/.")
        ]
    )


def load_boilerplate_components() -> str:
    """
    Reads all component source files from the boilerplate and returns
    them as a formatted string for injection into funnel_builder context.

    Includes:
      - /src/components/ui/*.tsx
      - /src/components/funnel/*.tsx
      - /src/lib/utils.ts
    """
    lines = ["=== COMPONENT SOURCE CODE ==="]

    ui_dir = BOILERPLATE_DIR / "src" / "components" / "ui"
    funnel_dir = BOILERPLATE_DIR / "src" / "components" / "funnel"
    utils_file = BOILERPLATE_DIR / "src" / "lib" / "utils.ts"

    if ui_dir.exists():
        for tsx_file in sorted(ui_dir.glob("*.tsx")):
            lines.append(f"\n--- /src/components/ui/{tsx_file.name} ---")
            lines.append(tsx_file.read_text(encoding="utf-8"))

    if funnel_dir.exists():
        for tsx_file in sorted(funnel_dir.glob("*.tsx")):
            lines.append(f"\n--- /src/components/funnel/{tsx_file.name} ---")
            lines.append(tsx_file.read_text(encoding="utf-8"))

    if utils_file.exists():
        lines.append("\n--- /src/lib/utils.ts ---")
        lines.append(utils_file.read_text(encoding="utf-8"))

    return "\n".join(lines)
