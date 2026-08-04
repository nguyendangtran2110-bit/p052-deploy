import asyncio
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.backend.core.config import get_settings
from src.backend.infrastructure.db.base import Base
from src.backend.infrastructure.db.models import (  # noqa: F401
    Conversation,
    KnowledgeChunk,
    KnowledgeDocument,
    Message,
    Resident,
    ResidentUnit,
    Ticket,
    TicketAttachment,
    TicketEvent,
    Unit,
)
from src.backend.infrastructure.db.session import normalize_async_database_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = normalize_async_database_url(get_settings().database_url)
config.set_main_option("sqlalchemy.url", database_url)
if database_url.startswith("sqlite") and ":memory:" not in database_url:
    sqlite_path = make_url(database_url).database
    if sqlite_path:
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
