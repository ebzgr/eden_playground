"""Player state tests."""

import pytest
from sqlalchemy import select

from playground.models.event import Event
from playground.models.user import User
from playground.services.player_state.service import patch_state, set_state


@pytest.mark.asyncio
async def test_patch_append_emits_state_changed(db_session):
    user = User(user_id_hash="statehash1", consent_state="granted")
    db_session.add(user)
    await db_session.flush()

    await patch_state(
        db_session,
        user,
        "journey.orbs",
        "append",
        "wisdom",
        "sess-ps-1",
        "deal_world",
        "intro",
    )
    await db_session.commit()

    result = await db_session.execute(
        select(Event).where(Event.event_type == "state_changed")
    )
    events = list(result.scalars().all())
    assert len(events) == 1
    assert events[0].payload["key"] == "journey.orbs"
    assert events[0].payload["new_value"] == ["wisdom"]
