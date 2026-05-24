"""Intro and map world entry flow."""

import pytest


@pytest.mark.asyncio
async def test_root_redirects_to_lab(client):
    r = await client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert "/worlds/intro_world/scenes/lab/view" in r.headers["location"]


@pytest.mark.asyncio
async def test_lab_scene_public_no_auth(client):
    r = await client.get("/worlds/intro_world/scenes/lab/view")
    assert r.status_code == 200
    assert b"Marketing for Betterment Lab" in r.content


@pytest.mark.asyncio
async def test_full_intro_to_map_flow(client):
    r = await client.get("/worlds/intro_world/scenes/lab/view")
    assert r.status_code == 200

    r = await client.post("/identity")
    code = r.json()["return_code"]
    headers = {"X-Return-Code": code}

    await client.post("/consent", json={"state": "granted"}, headers=headers)

    r = await client.get(
        "/worlds/intro_world/scenes/consent/view?session_id=test-sess",
        headers=headers,
    )
    assert r.status_code == 200
    assert b"Before we begin" in r.content

    r = await client.get(
        "/worlds/intro_world/scenes/demo/view?session_id=test-sess",
        headers=headers,
    )
    assert r.status_code == 200
    assert b"Mother Gaia" in r.content
    assert b"window.__DEMO__" in r.content
    assert b"Meet Mother Gaia" in r.content

    r = await client.get(
        "/worlds/map_world/scenes/welcome/view?session_id=map-sess",
        headers=headers,
    )
    assert r.status_code == 200
    assert b"Wonderful World of" in r.content
    assert b"Explore the map" in r.content
