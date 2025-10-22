from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _build_async_dsn() -> str:
    """Compute the asyncpg DSN without importing the full application settings."""

    direct_url = os.getenv("POSTGRES_ASYNC_DSN")
    if direct_url:
        return direct_url

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = quote_plus(os.getenv("POSTGRES_USER", "postgres"))
    password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
    database = quote_plus(os.getenv("POSTGRES_DATABASE", "chat_agent"))

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


# 使用异步 DSN，确保 Alembic 在线迁移时复用 asyncpg 驱动
config.set_main_option("sqlalchemy.url", _build_async_dsn())

target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""

    connectable: AsyncEngine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def main() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


main()
