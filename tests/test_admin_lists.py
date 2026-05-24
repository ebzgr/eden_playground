"""Admin users/experiments pagination, filters, and charts."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.experiment import Experiment
from playground.services.ab_testing.defaults import experiment_schedule
from playground.models.user import User
from playground.services.admin.charts import daily_new_users
from playground.services.admin.experiment_filters import ExperimentFilters
from playground.services.admin.service import (
    count_experiments,
    count_users,
    list_experiments,
    list_users,
)
from playground.services.admin.user_filters import UserFilters


@pytest.mark.asyncio
async def test_user_pagination_and_filters(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    for i in range(4):
        db_session.add(
            User(
                user_id_hash=f"user{i:02d}",
                consent_state="granted" if i % 2 == 0 else "pending",
                created_at=now - timedelta(days=i),
            )
        )
    await db_session.commit()

    f = UserFilters(consent_state="granted")
    assert await count_users(db_session, f) == 2
    page = await list_users(db_session, f, limit=1, offset=0)
    assert len(page) == 1
    assert page[0].consent_state == "granted"


@pytest.mark.asyncio
async def test_experiment_pagination_and_world_filter(db_session: AsyncSession):
    starts_at, ends_at = experiment_schedule()
    db_session.add_all(
        [
            Experiment(
                id="exp_a",
                name="Experiment A",
                target_scope="scene_version",
                assignment_scope="user",
                target={"world": "map_world", "scene": "x"},
                arms=[],
                state="live",
                starts_at=starts_at,
                ends_at=ends_at,
                explanation="",
            ),
            Experiment(
                id="exp_b",
                name="Experiment B",
                target_scope="scene_version",
                assignment_scope="user",
                target={"world": "deal_world", "scene": "y"},
                arms=[],
                state="draft",
                starts_at=starts_at,
                ends_at=ends_at,
                explanation="",
            ),
        ]
    )
    await db_session.commit()

    f = ExperimentFilters(world_id="map_world", state="live")
    assert await count_experiments(db_session, f) == 1
    rows = await list_experiments(db_session, f, limit=10, offset=0)
    assert rows[0].id == "exp_a"


@pytest.mark.asyncio
async def test_daily_new_users_chart_json(db_session: AsyncSession):
    db_session.add(User(user_id_hash="chartu1", consent_state="granted"))
    await db_session.commit()
    raw = await daily_new_users(db_session, days=7)
    assert '"labels"' in raw
    assert '"values"' in raw


@pytest.mark.asyncio
async def test_admin_users_page_has_chart(client):
    r = await client.get("/admin/users")
    assert r.status_code == 200
    assert b"users-daily-chart" in r.content
    assert b"chart.js" in r.content
    assert b"New users per day" in r.content


@pytest.mark.asyncio
async def test_admin_experiments_pagination(client):
    r = await client.get("/admin/experiments", params={"page_size": 25, "state": "live"})
    assert r.status_code == 200
    assert b"page_size=25" in r.content or b"Per page" in r.content
