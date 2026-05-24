"""Admin auth smoke test."""

import pytest
from httpx import BasicAuth


@pytest.mark.asyncio
async def test_admin_open_when_auth_disabled(client):
    r = await client.get("/admin/")
    assert r.status_code == 200
    assert b"Overview" in r.content or b"Events" in r.content


@pytest.mark.asyncio
async def test_admin_user_state_page(client):
    r = await client.post("/identity")
    user_id = r.json()["user_id"]
    r = await client.get(f"/admin/users/{user_id}/state")
    assert r.status_code == 200
