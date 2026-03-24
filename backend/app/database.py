from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
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
