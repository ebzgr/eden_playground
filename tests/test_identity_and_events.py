"""Identity, consent, and event tracker tests."""

import pytest


@pytest.mark.asyncio
async def test_identity_consent_and_events(client):
    r = await client.post("/identity")
    assert r.status_code == 200
    data = r.json()
    code = data["return_code"]
    headers = {"X-Return-Code": code}

    r = await client.post("/consent", json={"state": "granted"}, headers=headers)
    assert r.status_code == 200

    r = await client.post(
        "/events",
        json={
            "session_id": "sess-test-1",
            "events": [
                {
                    "event_type": "cta_click",
                    "world_id": "deal_world",
                    "scene_id": "intro",
                }
            ],
        },
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["accepted"] == 1
