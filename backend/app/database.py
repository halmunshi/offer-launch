from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _build_async_database_url(database_url: str) -> str:
    normalized_url = database_url

    if database_url.startswith("postgresql+asyncpg://"):
        normalized_url = database_url
    elif database_url.startswith("postgresql://"):
        normalized_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        normalized_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    split_url = urlsplit(normalized_url)
    query_params = parse_qsl(split_url.query, keep_blank_values=True)
    rewritten_query: list[tuple[str, str]] = []

    for key, value in query_params:
        if key == "sslmode":
            rewritten_query.append(("ssl", "require" if value != "disable" else "disable"))
            continue
        if key == "channel_binding":
            continue
        rewritten_query.append((key, value))

    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            urlencode(rewritten_query),
            split_url.fragment,
        )
    )


engine = create_async_engine(_build_async_database_url(settings.DATABASE_URL), future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
_last_connection_error: str | None = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_last_connection_error() -> str | None:
    return _last_connection_error


async def test_connection() -> bool:
    global _last_connection_error

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        _last_connection_error = None
        return True
    except Exception as error:
        _last_connection_error = str(error)
        return False
