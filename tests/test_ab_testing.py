"""A/B assignment tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.experiment import Experiment
from playground.models.user import User
from playground.services.ab_testing.defaults import experiment_schedule
from playground.services.ab_testing.service import resolve_scene_version


@pytest.mark.asyncio
async def test_seeded_assignment_is_stable(db_session: AsyncSession):
    user = User(user_id_hash="abc123", consent_state="granted")
    db_session.add(user)
    starts_at, ends_at = experiment_schedule()
    db_session.add(
        Experiment(
            id="exp_test",
            name="Test experiment",
            target_scope="scene_version",
            assignment_scope="user",
            target={"world": "deal_world", "scene": "intro"},
            arms=[
                {"id": "control", "version": "base", "weight": 50},
                {"id": "urgent", "version": "urgent", "weight": 50},
            ],
            state="live",
            starts_at=starts_at,
            ends_at=ends_at,
            explanation="Stable assignment test",
        )
    )
    await db_session.commit()

    a = await resolve_scene_version(
        db_session, "deal_world", "intro", "base", user.id, "sess-1"
    )
    b = await resolve_scene_version(
        db_session, "deal_world", "intro", "base", user.id, "sess-2"
    )
    assert a.version_id == b.version_id
    assert a.arm_id == b.arm_id


@pytest.mark.asyncio
async def test_three_arm_equal_weights(db_session: AsyncSession):
    """Arms list is not limited to two; equal weights split traffic ~1/3 each."""
    user = User(user_id_hash="multiarm", consent_state="granted")
    db_session.add(user)
    starts_at, ends_at = experiment_schedule()
    db_session.add(
        Experiment(
            id="exp_three",
            name="Three arm test",
            target_scope="scene_version",
            assignment_scope="user",
            target={"world": "intro_world", "scene": "consent"},
            arms=[
                {"id": "base", "version": "base", "weight": 1},
                {"id": "trust", "version": "trust", "weight": 1},
                {"id": "playful", "version": "playful", "weight": 1},
            ],
            state="live",
            starts_at=starts_at,
            ends_at=ends_at,
            explanation="Three-arm test",
        )
    )
    await db_session.commit()

    r = await resolve_scene_version(
        db_session, "intro_world", "consent", "base", user.id, "sess-1"
    )
    assert r.version_id in ("base", "trust", "playful")
    assert r.arm_id in ("base", "trust", "playful")
    assert r.experiment_id == "exp_three"
