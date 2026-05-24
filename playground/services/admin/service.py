"""Admin data queries."""

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.assignment import Assignment
from playground.models.event import Event
from playground.models.experiment import Experiment
from playground.models.player_state import PlayerState
from playground.models.user import User
from playground.services.admin.event_filters import EventFilters, apply_event_filters
from playground.services.admin.experiment_filters import (
    ExperimentFilters,
    apply_experiment_filters,
)
from playground.services.admin.user_filters import UserFilters, apply_user_filters


async def overview_stats(db: AsyncSession) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=1)
    events_today = await db.scalar(
        select(func.count(Event.id)).where(Event.ts_server >= since)
    )
    users_count = await db.scalar(select(func.count(User.id)))
    live_experiments = await db.scalar(
        select(func.count(Experiment.id)).where(Experiment.state == "live")
    )
    return {
        "events_today": events_today or 0,
        "users_count": users_count or 0,
        "live_experiments": live_experiments or 0,
    }


async def count_events(db: AsyncSession, filters: EventFilters) -> int:
    q = apply_event_filters(select(func.count(Event.id)), filters)
    return int(await db.scalar(q) or 0)


async def list_events(
    db: AsyncSession,
    filters: EventFilters | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Event]:
    q = (
        select(Event)
        .order_by(Event.ts_server.desc())
        .limit(limit)
        .offset(offset)
    )
    if filters:
        q = apply_event_filters(q, filters)
    result = await db.execute(q)
    return list(result.scalars().all())


async def event_filter_options(db: AsyncSession) -> dict:
    """Distinct values and experiment metadata for admin filter dropdowns."""
    worlds = [
        r[0]
        for r in (
            await db.execute(
                select(Event.world_id)
                .where(Event.world_id.isnot(None))
                .distinct()
                .order_by(Event.world_id)
            )
        ).all()
    ]
    scenes = [
        r[0]
        for r in (
            await db.execute(
                select(Event.scene_id)
                .where(Event.scene_id.isnot(None))
                .distinct()
                .order_by(Event.scene_id)
            )
        ).all()
    ]
    scene_pairs = [
        {"world_id": r[0], "scene_id": r[1]}
        for r in (
            await db.execute(
                select(Event.world_id, Event.scene_id)
                .where(Event.world_id.isnot(None), Event.scene_id.isnot(None))
                .distinct()
                .order_by(Event.world_id, Event.scene_id)
            )
        ).all()
    ]
    versions = [
        r[0]
        for r in (
            await db.execute(
                select(Event.scene_version_id)
                .where(Event.scene_version_id.isnot(None))
                .distinct()
                .order_by(Event.scene_version_id)
            )
        ).all()
    ]
    event_types = [
        r[0]
        for r in (
            await db.execute(
                select(Event.event_type).distinct().order_by(Event.event_type)
            )
        ).all()
    ]
    exp_rows = (
        await db.execute(select(Experiment).order_by(Experiment.id))
    ).scalars().all()
    experiments = [
        {
            "id": e.id,
            "state": e.state,
            "target": e.target,
            "arms": e.arms or [],
        }
        for e in exp_rows
    ]
    arm_ids: set[str] = set()
    for e in exp_rows:
        for arm in e.arms or []:
            if aid := arm.get("id"):
                arm_ids.add(aid)
    return {
        "worlds": worlds,
        "scenes": scenes,
        "scene_pairs": scene_pairs,
        "versions": versions,
        "event_types": event_types,
        "experiments": experiments,
        "arm_ids": sorted(arm_ids),
    }


def experiment_arm_label(experiment_arms: dict | list | None) -> str:
    """Compact display for table/CSV, e.g. ``exp_gaia:sky``."""
    if not experiment_arms or not isinstance(experiment_arms, dict):
        return ""
    parts = []
    for exp_id, meta in experiment_arms.items():
        if isinstance(meta, dict) and meta.get("arm_id"):
            parts.append(f"{exp_id}:{meta['arm_id']}")
        else:
            parts.append(str(exp_id))
    return "; ".join(parts)


def payload_preview(payload: dict | list | None, max_len: int = 120) -> str:
    if payload is None:
        return ""
    try:
        text = json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError):
        text = str(payload)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


async def count_users(db: AsyncSession, filters: UserFilters) -> int:
    q = apply_user_filters(select(func.count(User.id)), filters)
    return int(await db.scalar(q) or 0)


async def list_users(
    db: AsyncSession,
    filters: UserFilters | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[User]:
    q = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if filters:
        q = apply_user_filters(q, filters)
    result = await db.execute(q)
    return list(result.scalars().all())


async def user_filter_options(db: AsyncSession) -> dict:
    consent_states = [
        r[0]
        for r in (
            await db.execute(
                select(User.consent_state).distinct().order_by(User.consent_state)
            )
        ).all()
    ]
    return {"consent_states": consent_states}


async def count_experiments(db: AsyncSession, filters: ExperimentFilters) -> int:
    q = apply_experiment_filters(select(func.count(Experiment.id)), filters)
    return int(await db.scalar(q) or 0)


async def list_experiments(
    db: AsyncSession,
    filters: ExperimentFilters | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Experiment]:
    q = (
        select(Experiment)
        .order_by(Experiment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if filters:
        q = apply_experiment_filters(q, filters)
    result = await db.execute(q)
    return list(result.scalars().all())


async def experiment_filter_options(db: AsyncSession) -> dict:
    worlds: set[str] = set()
    for target in (await db.execute(select(Experiment.target))).scalars().all():
        if isinstance(target, dict) and target.get("world"):
            worlds.add(target["world"])
    return {
        "states": ["draft", "live", "paused", "done"],
        "target_scopes": ["scene_version"],
        "assignment_scopes": ["user", "session"],
        "worlds": sorted(worlds),
    }


async def user_state_rows(db: AsyncSession, user_id: UUID) -> list[PlayerState]:
    result = await db.execute(
        select(PlayerState).where(PlayerState.user_id == user_id)
    )
    return list(result.scalars().all())


async def experiment_arm_counts(db: AsyncSession, experiment_id: str) -> dict[str, int]:
    result = await db.execute(
        select(Assignment.arm_id, func.count())
        .where(Assignment.experiment_id == experiment_id)
        .group_by(Assignment.arm_id)
    )
    return {row[0]: row[1] for row in result.all()}
