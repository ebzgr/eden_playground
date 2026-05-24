"""Experiment schedule, status transitions, and audit history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.experiment import Experiment
from playground.models.experiment_status_history import ExperimentStatusHistory

VALID_STATES = frozenset({"draft", "live", "paused", "done"})


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    """Normalize DB datetimes (SQLite may return naive) for comparison."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _ends_expired(exp: Experiment, now: datetime | None = None) -> bool:
    now = now or utcnow()
    return as_utc(exp.ends_at) <= now


async def record_history(
    db: AsyncSession,
    experiment_id: str,
    action: str,
    *,
    previous_state: str | None = None,
    new_state: str | None = None,
    previous_ends_at: datetime | None = None,
    new_ends_at: datetime | None = None,
    note: str | None = None,
) -> None:
    db.add(
        ExperimentStatusHistory(
            experiment_id=experiment_id,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            previous_ends_at=previous_ends_at,
            new_ends_at=new_ends_at,
            note=note,
        )
    )


async def finish_if_expired(db: AsyncSession, exp: Experiment) -> bool:
    """If past ``ends_at`` and not already done, set state to done and log."""
    if exp.state == "done":
        return False
    if exp.state not in ("live", "paused"):
        return False
    if not _ends_expired(exp):
        return False
    prev = exp.state
    exp.state = "done"
    await record_history(
        db,
        exp.id,
        "finished",
        previous_state=prev,
        new_state="done",
        note="End date reached (automatic).",
    )
    return True


async def sync_expired_experiments(db: AsyncSession) -> int:
    """Mark all past-end live/paused experiments as done. Returns count changed."""
    result = await db.execute(
        select(Experiment).where(Experiment.state.in_(("live", "paused")))
    )
    changed = 0
    for exp in result.scalars().all():
        if await finish_if_expired(db, exp):
            changed += 1
    if changed:
        await db.flush()
    return changed


def experiment_is_assignable(exp: Experiment, now: datetime | None = None) -> bool:
    """True when experiment should assign scene versions to users."""
    now = now or utcnow()
    return (
        exp.state == "live"
        and as_utc(exp.starts_at) <= now
        and as_utc(exp.ends_at) > now
    )


async def set_experiment_state(
    db: AsyncSession,
    exp: Experiment,
    new_state: str,
    *,
    note: str | None = None,
) -> None:
    if new_state not in VALID_STATES:
        raise ValueError(f"invalid state: {new_state}")
    prev = exp.state
    if prev == new_state:
        return
    exp.state = new_state
    action = {
        "live": "live",
        "paused": "paused",
        "done": "finished",
        "draft": "draft",
    }.get(new_state, "status_change")
    await record_history(
        db,
        exp.id,
        action,
        previous_state=prev,
        new_state=new_state,
        note=note,
    )


async def extend_experiment(
    db: AsyncSession,
    exp: Experiment,
    extra_days: int,
    *,
    note: str | None = None,
) -> datetime:
    if extra_days < 1:
        raise ValueError("extra_days must be at least 1")
    prev_end = as_utc(exp.ends_at)
    new_end = prev_end + timedelta(days=extra_days)
    exp.ends_at = new_end
    await record_history(
        db,
        exp.id,
        "extended",
        previous_state=exp.state,
        new_state=exp.state,
        previous_ends_at=prev_end,
        new_ends_at=new_end,
        note=note or f"Extended by {extra_days} day(s).",
    )
    return new_end


async def list_experiment_history(
    db: AsyncSession, experiment_id: str
) -> list[ExperimentStatusHistory]:
    result = await db.execute(
        select(ExperimentStatusHistory)
        .where(ExperimentStatusHistory.experiment_id == experiment_id)
        .order_by(ExperimentStatusHistory.created_at.desc())
    )
    return list(result.scalars().all())
