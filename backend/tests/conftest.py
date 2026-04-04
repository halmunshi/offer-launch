import os
import sys
import types
import uuid
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi import Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.database import get_db
from app.middleware.clerk_auth import get_current_user
from app.models.enums import UserPlan
from app.models.user import User

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    split_url = urlsplit(database_url)
    query_params = parse_qsl(split_url.query, keep_blank_values=True)
    rewritten_query: list[tuple[str, str]] = []

    for key, param_value in query_params:
        if key == "sslmode":
            rewritten_query.append(("ssl", "require" if param_value != "disable" else "disable"))
            continue
        if key == "channel_binding":
            continue
        rewritten_query.append((key, param_value))

    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            urlencode(rewritten_query),
            split_url.fragment,
        )
    )


@pytest.fixture(scope="session")
def database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set")
    return _normalize_database_url(database_url)


@pytest_asyncio.fixture
async def test_engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(bind=connection, expire_on_commit=False)
    await session.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_nested_savepoint(sess, trans) -> None:
        if trans.nested and trans.parent is not None and not trans.parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
def app_instance():
    from app.main import app

    return app


@pytest.fixture
def reset_limiter_state() -> None:
    try:
        from app.limiter import limiter

        storage = getattr(limiter, "_storage", None)
        if storage is not None and hasattr(storage, "reset"):
            storage.reset()
    except Exception:
        pass


def _auth_override(user: User):
    async def _override(request: Request) -> User:
        request.state.user_id = str(user.id)
        return user

    return _override


@pytest_asyncio.fixture
async def primary_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        clerk_id=f"clerk_{uuid.uuid4().hex}",
        email=f"primary_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Primary Test User",
        avatar_url="https://example.com/avatar-primary.png",
        plan=UserPlan.free,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def secondary_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        clerk_id=f"clerk_{uuid.uuid4().hex}",
        email=f"secondary_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Secondary Test User",
        avatar_url="https://example.com/avatar-secondary.png",
        plan=UserPlan.free,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def pro_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        clerk_id=f"clerk_{uuid.uuid4().hex}",
        email=f"pro_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Pro Test User",
        avatar_url="https://example.com/avatar-pro.png",
        plan=UserPlan.pro,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
def set_current_user(app_instance) -> Callable[[User], None]:
    def _set(user: User) -> None:
        app_instance.dependency_overrides[get_current_user] = _auth_override(user)

    return _set


@pytest_asyncio.fixture
async def api_client(
    app_instance,
    db_session: AsyncSession,
    primary_user: User,
    set_current_user: Callable[[User], None],
    reset_limiter_state,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app_instance.dependency_overrides[get_db] = _override_get_db
    set_current_user(primary_user)

    transport = httpx.ASGITransport(app=app_instance, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app_instance.dependency_overrides.clear()


@pytest.fixture
def valid_intake_data() -> dict:
    return {
        "role": "coach",
        "industry": "business coaching",
        "brand_name": "Elite Coach Co",
        "credibility": "200+ coaches trained",
        "offer_name": "Six Figure Coach Academy",
        "offer_one_liner": "Build a 6-figure coaching business in 90 days",
        "price_point": "2997",
        "whats_included": "8-week live program, weekly group calls, templates",
        "unique_mechanism": "The Client Acquisition System",
        "transformation": "From zero clients to full roster in 90 days",
        "ideal_client": "Coaches with expertise but no consistent pipeline",
        "age_ranges": ["25-34", "35-44"],
        "pain_point": "No predictable way to get clients",
        "awareness_level": "solution-aware",
        "has_testimonials": True,
        "testimonials": ["Sarah M got first 3k client in week 2"],
        "assets": ["logo", "case_studies"],
        "has_guarantee": True,
        "guarantee_type": "money_back",
        "guarantee_duration": "30 days",
        "copy_style": "bold",
        "funnel_type": "vsl",
        "theme": "direct-response",
        "selected_pages": ["vsl", "order", "thank_you"],
    }


@pytest.fixture
def celery_mock_calls(monkeypatch) -> list[dict]:
    calls: list[dict] = []

    class _DummyResult:
        id = "mock-task-id"

    def _record(method: str):
        def _inner(*args, **kwargs):
            calls.append({"method": method, "args": args, "kwargs": kwargs})
            return _DummyResult()

        return _inner

    fake_tasks_module = types.ModuleType("app.workers.tasks")
    fake_tasks_module.generate_funnel_task = types.SimpleNamespace(
        apply_async=_record("apply_async"),
        delay=_record("delay"),
    )
    monkeypatch.setitem(sys.modules, "app.workers.tasks", fake_tasks_module)

    return calls


@pytest.fixture(autouse=True)
def _autouse_celery_mock(celery_mock_calls):
    _ = celery_mock_calls
    yield
