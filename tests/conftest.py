"""Pytest fixtures."""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_playground.db"

from playground.config import get_settings

get_settings.cache_clear()

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from playground.db import Base, get_db
from playground.main import app
from playground.seed import _ensure_demo_experiment, _sync_worlds_from_disk

TEST_DB_URL = os.environ["DATABASE_URL"]


@pytest.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def db_session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _sync_worlds_from_disk(session)
        await _ensure_demo_experiment(session)
        await session.commit()
        yield session


@pytest.fixture
async def client(engine, db_session):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
