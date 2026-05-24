"""Admin helpers for experiment CRUD and lifecycle actions."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.experiment import Experiment
from playground.services.ab_testing.lifecycle import (
    extend_experiment,
    list_experiment_history,
    record_history,
    set_experiment_state,
    sync_expired_experiments,
    utcnow,
)


def parse_admin_datetime(value: str) -> datetime:
    """Parse ``datetime-local`` form value as UTC."""
    dt = datetime.fromisoformat(value.strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def default_schedule() -> tuple[datetime, datetime]:
    now = utcnow()
    return now, now + timedelta(days=14)


def slugify_experiment_id(name: str) -> str:
    """Build a stable technical id from a display name."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    if not slug:
        raise ValueError("Name must contain at least one letter or number.")
    return slug if slug.startswith("exp_") else f"exp_{slug}"


def resolve_experiment_id(name: str, explicit_id: str | None) -> str:
    """Use explicit id when provided, otherwise derive from name."""
    if explicit_id and explicit_id.strip():
        return explicit_id.strip()
    return slugify_experiment_id(name)


def parse_arms_from_form(
    arm_ids: list[str],
    arm_versions: list[str],
    arm_weights: list[int],
) -> list[dict]:
    if not arm_ids:
        raise ValueError("Add at least one arm.")
    arms: list[dict] = []
    for i, arm_id in enumerate(arm_ids):
        aid = (arm_id or "").strip()
        if not aid:
            continue
        try:
            version = (arm_versions[i] if i < len(arm_versions) else "").strip()
            weight = int(arm_weights[i] if i < len(arm_weights) else 1)
        except (IndexError, ValueError) as exc:
            raise ValueError(f"Invalid arm row {i + 1}.") from exc
        if not version:
            raise ValueError(f"Arm “{aid}” needs a scene version.")
        if weight < 1:
            raise ValueError(f"Arm “{aid}” weight must be at least 1.")
        arms.append({"id": aid, "version": version, "weight": weight})
    if len(arms) < 2:
        raise ValueError("At least two arms are required for an A/B test.")
    return arms


async def create_experiment(
    db: AsyncSession,
    *,
    id: str,
    name: str,
    assignment_scope: str,
    world: str,
    scene: str,
    arms: list[dict],
    explanation: str,
    starts_at: datetime,
    ends_at: datetime,
    state: str = "draft",
) -> Experiment:
    if ends_at <= starts_at:
        raise ValueError("End must be after start.")
    display_name = name.strip()
    if not display_name:
        raise ValueError("Experiment name is required.")
    if await db.get(Experiment, id):
        raise ValueError(f"Experiment id “{id}” already exists.")
    exp = Experiment(
        id=id,
        name=display_name,
        target_scope="scene_version",
        assignment_scope=assignment_scope,
        target={"world": world, "scene": scene},
        arms=arms,
        state=state,
        starts_at=starts_at,
        ends_at=ends_at,
        explanation=explanation.strip(),
    )
    db.add(exp)
    await db.flush()
    await record_history(
        db,
        id,
        "created",
        new_state=state,
        new_ends_at=ends_at,
        note=f"Created “{display_name}”. Scheduled {starts_at.date()} → {ends_at.date()}.",
    )
    return exp


async def get_experiment_detail_context(
    db: AsyncSession, exp_id: str
) -> dict | None:
    await sync_expired_experiments(db)
    exp = await db.get(Experiment, exp_id)
    if not exp:
        return None
    history = await list_experiment_history(db, exp_id)
    return {"experiment": exp, "history": history}
