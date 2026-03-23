import asyncio
from logging.config import fileConfig
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config import settings
from app.database import Base
import app.models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_migration_url() -> str:
    migration_url = settings.DATABASE_URL_DIRECT or settings.DATABASE_URL
    if migration_url.startswith("postgresql+asyncpg://"):
        return migration_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return migration_url


def get_async_migration_url() -> str:
    migration_url = get_migration_url()
    if migration_url.startswith("postgres://"):
        migration_url = migration_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif migration_url.startswith("postgresql://"):
        migration_url = migration_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    split_url = urlsplit(migration_url)
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


def run_migrations_offline() -> None:
    url = get_migration_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_async_migration_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
