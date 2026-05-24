"""Event handler ingest and preview gating."""

import pytest
from sqlalchemy import select

from playground.models.event import Event


@pytest.mark.asyncio
async def test_scene_exit_event_persists_with_payload(client):
    r = await client.post("/identity")
    code = r.json()["return_code"]
    headers = {"X-Return-Code": code}

    await client.post("/consent", json={"state": "granted"}, headers=headers)

    r = await client.post(
        "/events",
        json={
            "session_id": "sess-exit-1",
            "events": [
                {
                    "event_type": "scene_exit",
                    "world_id": "intro_world",
                    "scene_id": "consent",
                    "scene_version_id": "base",
                    "experiment_arms": {
                        "exp_test": {"arm_id": "trust", "assignment_scope": "user"}
                    },
                    "payload": {"duration_ms": 1234, "reason": "nav"},
                }
            ],
        },
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["accepted"] == 1


@pytest.mark.asyncio
async def test_preview_header_drops_events(client):
    r = await client.post("/identity")
    code = r.json()["return_code"]
    headers = {"X-Return-Code": code, "X-Playground-Preview": "1"}

    await client.post("/consent", json={"state": "granted"}, headers=headers)

    r = await client.post(
        "/events",
        json={
            "session_id": "preview-intro_world",
            "events": [
                {
                    "event_type": "scene_view",
                    "world_id": "intro_world",
                    "scene_id": "lab",
                }
            ],
        },
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["accepted"] == 0


@pytest.mark.asyncio
async def test_scene_exit_stored_fields(db_session, client):
    """Verify scene_exit row shape after ingest via API."""
    r = await client.post("/identity")
    code = r.json()["return_code"]
    headers = {"X-Return-Code": code}
    await client.post("/consent", json={"state": "granted"}, headers=headers)

    await client.post(
        "/events",
        json={
            "session_id": "sess-exit-2",
            "events": [
                {
                    "event_type": "scene_exit",
                    "world_id": "map_world",
                    "scene_id": "welcome",
                    "scene_version_id": "base",
                    "payload": {"duration_ms": 500, "reason": "hidden"},
                }
            ],
        },
        headers=headers,
    )

    result = await db_session.execute(
        select(Event).where(Event.event_type == "scene_exit")
    )
    rows = result.scalars().all()
    assert any(e.scene_id == "welcome" for e in rows)
    row = next(e for e in rows if e.scene_id == "welcome")
    assert row.payload["duration_ms"] == 500
    assert row.payload["reason"] == "hidden"
    assert row.scene_version_id == "base"
