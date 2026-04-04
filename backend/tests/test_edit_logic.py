import pytest

from app.agents import tools


@pytest.mark.asyncio
async def test_edit_funnel_file_returns_not_found_when_file_missing(monkeypatch) -> None:
    async def _read_missing(path: str, funnel_id: str, db) -> str:
        _ = (path, funnel_id, db)
        return ""

    monkeypatch.setattr(tools, "_read_funnel_file_impl", _read_missing)

    result = await tools._edit_funnel_file_impl(
        path="/src/App.tsx",
        old_str="old",
        new_str="new",
        funnel_id="funnel-1",
        db=object(),
    )

    assert result == "File /src/App.tsx not found. Use write_funnel_file to create it."


@pytest.mark.asyncio
async def test_edit_funnel_file_requires_exact_old_string(monkeypatch) -> None:
    async def _read_existing(path: str, funnel_id: str, db) -> str:
        _ = (path, funnel_id, db)
        return "const headline = 'Hello world'"

    monkeypatch.setattr(tools, "_read_funnel_file_impl", _read_existing)

    result = await tools._edit_funnel_file_impl(
        path="/src/App.tsx",
        old_str="missing",
        new_str="replacement",
        funnel_id="funnel-1",
        db=object(),
    )

    assert result == (
        "String not found in /src/App.tsx. Call read_funnel_file first and "
        "use the exact text you want to replace."
    )


@pytest.mark.asyncio
async def test_edit_funnel_file_replaces_first_occurrence_only(monkeypatch) -> None:
    writes: list[tuple[str, str, str]] = []

    async def _read_existing(path: str, funnel_id: str, db) -> str:
        _ = db
        assert path == "/src/App.tsx"
        assert funnel_id == "funnel-1"
        return "OLD and another OLD"

    async def _capture_write(path: str, content: str, funnel_id: str, db) -> str:
        _ = db
        writes.append((path, content, funnel_id))
        return f"Written: {path}"

    monkeypatch.setattr(tools, "_read_funnel_file_impl", _read_existing)
    monkeypatch.setattr(tools, "_write_funnel_file_impl", _capture_write)

    result = await tools._edit_funnel_file_impl(
        path="/src/App.tsx",
        old_str="OLD",
        new_str="NEW",
        funnel_id="funnel-1",
        db=object(),
    )

    assert result == "Edited: /src/App.tsx"
    assert writes == [("/src/App.tsx", "NEW and another OLD", "funnel-1")]
