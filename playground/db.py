"""SQLAlchemy async engine and session factory."""

from collections.abc import AsyncGenerator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from playground.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def _alembic_config() -> Config:
    root = Path(__file__).resolve().parent.parent
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def _legacy_db_without_alembic(sync_conn) -> bool:
    """True when tables were created via create_all before Alembic was wired in."""
    insp = inspect(sync_conn)
    return insp.has_table("users") and not insp.has_table("alembic_version")


def _run_migrations(sync_conn) -> None:
    cfg = _alembic_config()
    cfg.attributes["connection"] = sync_conn
    if _legacy_db_without_alembic(sync_conn):
        command.stamp(cfg, "001")
    command.upgrade(cfg, "head")


async def init_db() -> None:
    """Apply Alembic migrations (canonical schema management)."""
    async with engine.begin() as conn:
        await conn.run_sync(_run_migrations)
