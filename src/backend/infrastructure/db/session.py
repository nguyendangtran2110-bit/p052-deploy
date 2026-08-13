from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.backend.core.config import get_settings
from src.backend.infrastructure.db.base import Base


def normalize_async_database_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


settings = get_settings()
database_url = normalize_async_database_url(settings.database_url)
engine_options: dict = {"echo": settings.database_echo, "pool_pre_ping": True}

if database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
    if ":memory:" in database_url:
        engine_options["poolclass"] = StaticPool

engine = create_async_engine(database_url, **engine_options)
SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    # Import models before create_all so every table is registered in metadata.
    from src.backend.infrastructure.db import models  # noqa: F401

    if database_url.startswith("sqlite") and ":memory:" not in database_url:
        sqlite_path = make_url(database_url).database
        if sqlite_path:
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    from src.backend.infrastructure.db import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    await engine.dispose()
