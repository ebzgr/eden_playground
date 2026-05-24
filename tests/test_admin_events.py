"""Admin events page filters and CSV export."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.event import Event
from playground.models.user import User
from playground.services.admin.event_filters import EventFilters
from playground.services.admin.service import count_events, list_events


@pytest.mark.asyncio
async def test_event_filters_world_and_type(db_session: AsyncSession):
    user = User(user_id_hash="filteruser", consent_state="granted")
    db_session.add(user)
    await db_session.flush()

    db_session.add_all(
        [
            Event(
                user_id=user.id,
                session_id="s1",
                world_id="map_world",
                scene_id="welcome",
                scene_version_id="base",
                event_type="scene_view",
                experiment_arms={
                    "exp_consent_copy": {"arm_id": "trust"}
                },
                payload={"x": 1},
                ts_server=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
            ),
            Event(
                user_id=user.id,
                session_id="s1",
                world_id="intro_world",
                scene_id="lab",
                scene_version_id="base",
                event_type="intro_lab_continue",
                payload={},
                ts_server=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    await db_session.commit()

    f = EventFilters(world_id="map_world", event_type="scene_view")
    assert await count_events(db_session, f) == 1
    rows = await list_events(db_session, f, limit=10)
    assert len(rows) == 1
    assert rows[0].scene_version_id == "base"


@pytest.mark.asyncio
async def test_event_filters_experiment_and_arm(db_session: AsyncSession):
    user = User(user_id_hash="armfilter", consent_state="granted")
    db_session.add(user)
    await db_session.flush()

    db_session.add(
        Event(
            user_id=user.id,
            session_id="s1",
            world_id="map_world",
            scene_id="welcome",
            scene_version_id="base",
            event_type="scene_view",
            experiment_arms={
                "exp_consent_copy": {
                    "arm_id": "playful",
                    "assignment_scope": "user",
                }
            },
            ts_server=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    f = EventFilters(
        experiment_id="exp_consent_copy", arm_id="playful"
    )
    assert await count_events(db_session, f) == 1

    f_miss = EventFilters(
        experiment_id="exp_consent_copy", arm_id="trust"
    )
    assert await count_events(db_session, f_miss) == 0


@pytest.mark.asyncio
async def test_admin_events_page_and_filtered_csv(client):
    r = await client.post("/identity")
    code = r.json()["return_code"]
    headers = {"X-Return-Code": code}
    await client.post("/consent", json={"state": "granted"}, headers=headers)
    await client.post(
        "/events",
        headers=headers,
        json={
            "session_id": "csv-sess",
            "events": [
                {
                    "event_type": "test_filter_event",
                    "world_id": "map_world",
                    "scene_id": "welcome",
                    "scene_version_id": "base",
                }
            ],
        },
    )

    r = await client.get(
        "/admin/events",
        params={"world_id": "map_world", "event_type": "test_filter_event"},
    )
    assert r.status_code == 200
    assert b"test_filter_event" in r.content
    assert b"Download CSV" in r.content
    assert b"world_id=map_world" in r.content

    r = await client.get(
        "/admin/events/export",
        params={"world_id": "map_world", "event_type": "test_filter_event"},
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    body = r.content.decode()
    assert "test_filter_event" in body
    assert "map_world" in body
    assert "intro_lab_continue" not in body


@pytest.mark.asyncio
async def test_events_pagination_limits_rows(db_session: AsyncSession):
    user = User(user_id_hash="paginate", consent_state="granted")
    db_session.add(user)
    await db_session.flush()
    for i in range(5):
        db_session.add(
            Event(
                user_id=user.id,
                session_id="s1",
                world_id="map_world",
                event_type="paginated_evt",
                ts_server=datetime(2026, 5, 22, i, 0, tzinfo=timezone.utc),
            )
        )
    await db_session.commit()

    page1 = await list_events(db_session, EventFilters(event_type="paginated_evt"), limit=2, offset=0)
    page2 = await list_events(db_session, EventFilters(event_type="paginated_evt"), limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].id != page2[0].id


@pytest.mark.asyncio
async def test_admin_events_page_uses_bootstrap_and_page_size(client):
    r = await client.get("/admin/events", params={"page_size": 25})
    assert r.status_code == 200
    assert b"bootstrap" in r.content
    assert b"Per page" in r.content
    assert b"page_size" in r.content
