"""End-to-end happy path across services."""

import pytest


@pytest.mark.asyncio
async def test_e2e_scene_event_state_transition(client):
    r = await client.post("/identity")
    code = r.json()["return_code"]
    headers = {"X-Return-Code": code}

    await client.post("/consent", json={"state": "granted"}, headers=headers)

    r = await client.get(
        "/worlds/deal_world/scenes/intro",
        headers=headers,
    )
    assert r.status_code == 200
    scene = r.json()
    assert scene["version_id"] in ("base", "urgent")
    session_id = scene["session_id"]

    r = await client.post(
        "/events",
        json={
            "session_id": session_id,
            "events": [{"event_type": "scene_view", "world_id": "deal_world", "scene_id": "intro"}],
        },
        headers=headers,
    )
    assert r.json()["accepted"] == 1

    r = await client.patch(
        f"/state/journey.orbs?session_id={session_id}",
        json={"op": "append", "value": "wisdom"},
        headers={**headers, "X-World-Id": "deal_world", "X-Scene-Id": "intro"},
    )
    assert r.status_code == 200
    assert "wisdom" in r.json()["value"]

    r = await client.post(
        "/worlds/deal_world/scenes/intro/transition",
        json={"event": "cta_click", "session_id": session_id},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["next_scene"] == "checkout"
