"""Experiment schedule, expiry, extend, and history."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.experiment import Experiment
from playground.services.ab_testing.defaults import experiment_schedule
from playground.services.ab_testing.lifecycle import (
    extend_experiment,
    finish_if_expired,
    list_experiment_history,
    set_experiment_state,
    sync_expired_experiments,
)
from playground.services.ab_testing.service import resolve_scene_version
from playground.models.user import User


def _live_exp(**overrides) -> Experiment:
    starts, ends = experiment_schedule(duration_days=30)
    data = {
        "id": "exp_lifecycle",
        "name": "Lifecycle test",
        "target_scope": "scene_version",
        "assignment_scope": "user",
        "target": {"world": "lifecycle_world", "scene": "only_scene"},
        "arms": [{"id": "control", "version": "base", "weight": 100}],
        "state": "live",
        "starts_at": starts,
        "ends_at": ends,
        "explanation": "Lifecycle test",
    }
    data.update(overrides)
    return Experiment(**data)


@pytest.mark.asyncio
async def test_finish_if_expired_marks_done(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    exp = _live_exp(ends_at=now - timedelta(hours=1))
    db_session.add(exp)
    await db_session.flush()
    changed = await finish_if_expired(db_session, exp)
    assert changed is True
    assert exp.state == "done"
    history = await list_experiment_history(db_session, exp.id)
    assert history[0].action == "finished"


@pytest.mark.asyncio
async def test_sync_expired_experiments(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    db_session.add(
        _live_exp(id="exp_old", ends_at=now - timedelta(days=1))
    )
    db_session.add(_live_exp(id="exp_ok", ends_at=now + timedelta(days=7)))
    await db_session.flush()
    n = await sync_expired_experiments(db_session)
    assert n == 1


@pytest.mark.asyncio
async def test_extend_records_history(db_session: AsyncSession):
    exp = _live_exp()
    db_session.add(exp)
    await db_session.flush()
    prev_end = exp.ends_at
    new_end = await extend_experiment(db_session, exp, 14, note="More traffic needed")
    assert new_end == prev_end + timedelta(days=14)
    history = await list_experiment_history(db_session, exp.id)
    assert any(h.action == "extended" for h in history)


@pytest.mark.asyncio
async def test_set_state_records_pause_and_live(db_session: AsyncSession):
    exp = _live_exp(state="draft")
    db_session.add(exp)
    await db_session.flush()
    await set_experiment_state(db_session, exp, "live", note="Launch")
    await set_experiment_state(db_session, exp, "paused", note="Hold")
    history = await list_experiment_history(db_session, exp.id)
    actions = {h.action for h in history}
    assert "live" in actions
    assert "paused" in actions


@pytest.mark.asyncio
async def test_expired_experiment_not_assigned(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    user = User(user_id_hash="expired_user", consent_state="granted")
    db_session.add(user)
    db_session.add(
        _live_exp(ends_at=now - timedelta(minutes=5))
    )
    await db_session.commit()
    await sync_expired_experiments(db_session)
    await db_session.commit()
    r = await resolve_scene_version(
        db_session, "lifecycle_world", "only_scene", "base", user.id, "s1"
    )
    assert r.experiment_id is None
    assert r.version_id == "base"
