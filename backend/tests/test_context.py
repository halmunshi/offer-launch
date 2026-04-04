from app.agents.context import build_agent_context, build_session_context, list_funnel_file_paths


def test_build_agent_context_returns_none_for_empty_intake() -> None:
    assert build_agent_context(agent_type="copywriter", intake=None) is None


def test_build_agent_context_contains_key_offer_fields() -> None:
    intake = {
        "offer_name": "Six Figure Coach Academy",
        "offer_one_liner": "Build a 6-figure coaching business in 90 days",
        "brand_name": "Elite Coach Co",
        "industry": "business coaching",
        "role": "coach",
        "price_point": "2997",
        "funnel_type": "vsl",
        "copy_style": "bold",
        "theme": "direct-response",
        "whats_included": "8-week live program",
        "unique_mechanism": "The Client Acquisition System",
        "transformation": "From zero clients to full roster",
        "ideal_client": "Coaches",
        "pain_point": "No predictable way to get clients",
        "awareness_level": "solution-aware",
        "testimonials": ["Sarah M"],
        "assets_available": ["logo"],
        "guarantee": "30 day guarantee",
    }

    result = build_agent_context(agent_type="copywriter", intake=intake)

    assert isinstance(result, str)
    assert "Six Figure Coach Academy" in result
    assert "business coaching" in result
    assert "Funnel type: vsl" in result
    assert "Mechanism: The Client Acquisition System" in result


def test_build_agent_context_handles_missing_optional_fields_safely() -> None:
    intake = {
        "offer_name": "Minimal Offer",
        "industry": "coaching",
        "funnel_type": "vsl",
    }

    result = build_agent_context(agent_type="copywriter", intake=intake)

    assert isinstance(result, str)
    assert "Minimal Offer" in result
    assert "Industry: coaching" in result


def test_build_agent_context_large_payload_current_behavior() -> None:
    intake = {
        "offer_name": "x" * 100,
        "offer_one_liner": "y" * 300,
        "brand_name": "b" * 100,
        "industry": "i" * 100,
        "role": "r" * 50,
        "price_point": "2997",
        "funnel_type": "vsl",
        "copy_style": "bold",
        "theme": "direct-response",
        "whats_included": "w" * 3000,
        "unique_mechanism": "m" * 2000,
        "transformation": "t" * 2000,
        "ideal_client": "c" * 2000,
        "age_ranges": ["25-34", "35-44"],
        "pain_point": "p" * 2000,
        "awareness_level": "solution-aware",
        "testimonials": ["testimony" * 100],
        "assets_available": ["logo", "case_studies"],
        "guarantee": "g" * 2000,
    }

    result = build_agent_context(agent_type="copywriter", intake=intake)

    assert isinstance(result, str)
    assert len(result) > 10000


def test_build_session_context_returns_none_when_all_empty() -> None:
    result = build_session_context(
        session_summary=None,
        recent_messages=[],
        all_messages=[],
        file_paths=[],
    )

    assert result is None


def test_build_session_context_summary_only() -> None:
    result = build_session_context(
        session_summary="Prior session summary",
        recent_messages=[],
        all_messages=[],
        file_paths=[],
    )

    assert isinstance(result, str)
    assert "=== PREVIOUS SESSION ===" in result
    assert "Prior session summary" in result


def test_build_session_context_contains_all_sections() -> None:
    result = build_session_context(
        session_summary="Summary text",
        recent_messages=[{"role": "user", "content": "hello"}],
        all_messages=[],
        file_paths=["/src/pages/Vsl.tsx", "/src/main.tsx"],
    )

    assert isinstance(result, str)
    assert "=== PREVIOUS SESSION ===" in result
    assert "=== RECENT MESSAGES ===" in result
    assert "=== CURRENT FILES ===" in result


def test_build_session_context_formats_roles() -> None:
    recent_messages = [
        {"role": "user", "content": "user says hi"},
        {"role": "agent", "content": "agent reply"},
        {
            "role": "tool_call",
            "content": "write_funnel_file",
            "metadata": {"tool_name": "write_funnel_file", "path": "/src/theme.ts"},
        },
        {
            "role": "tool_result",
            "content": "Written",
            "metadata": {"path": "/src/theme.ts", "status": "updated"},
        },
    ]

    result = build_session_context(
        session_summary="Summary",
        recent_messages=recent_messages,
        all_messages=[],
        file_paths=[],
    )

    assert isinstance(result, str)
    assert "USER: user says hi" in result
    assert "AGENT: agent reply" in result
    assert "TOOL: write_funnel_file -> /src/theme.ts" in result
    assert "RESULT: OK /src/theme.ts (updated)" in result


def test_build_session_context_message_truncation_current_behavior() -> None:
    # TODO: when app logic changes from 400 -> 300 chars, update this assertion.
    long_content = "x" * 1000
    result = build_session_context(
        session_summary="Summary",
        recent_messages=[{"role": "user", "content": long_content}],
        all_messages=[],
        file_paths=[],
    )

    assert isinstance(result, str)
    assert f"USER: {'x' * 400}" in result
    assert f"USER: {'x' * 401}" not in result


def test_list_funnel_file_paths_filters_internal_paths() -> None:
    files = {
        "/src/App.tsx": {"code": "..."},
        "/node_modules/react/index.js": {"code": "..."},
        "/.claude/CLAUDE.md": {"code": "..."},
        "/src/pages/Vsl.tsx": {"code": "..."},
    }

    result = list_funnel_file_paths(files)

    assert "/src/App.tsx" in result
    assert "/src/pages/Vsl.tsx" in result
    assert "/node_modules/react/index.js" not in result
    assert "/.claude/CLAUDE.md" not in result
