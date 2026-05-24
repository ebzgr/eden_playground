"""Experiment lookup and scene-version assignment (no navigation A/B)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.assignment import Assignment
from playground.models.experiment import Experiment
from playground.schemas.experiment import SceneAssignmentResponse
from playground.services.ab_testing.assigner import pick_arm
from playground.services.ab_testing.lifecycle import (
    experiment_is_assignable,
    finish_if_expired,
    utcnow,
)


async def _find_active_scene_experiment(
    db: AsyncSession,
    world_id: str,
    scene_id: str,
) -> Experiment | None:
    result = await db.execute(
        select(Experiment).where(
            Experiment.target_scope == "scene_version",
            Experiment.state.in_(("live", "paused")),
        )
    )
    now = utcnow()
    for exp in result.scalars().all():
        t = exp.target or {}
        if t.get("world") != world_id or t.get("scene") != scene_id:
            continue
        if await finish_if_expired(db, exp):
            continue
        if experiment_is_assignable(exp, now):
            return exp
    return None


async def _get_or_assign_arm(
    db: AsyncSession,
    experiment: Experiment,
    subject_type: str,
    subject_id: str,
) -> dict:
    if experiment.assignment_scope == "user":
        result = await db.execute(
            select(Assignment).where(
                Assignment.experiment_id == experiment.id,
                Assignment.subject_type == subject_type,
                Assignment.subject_id == subject_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            for arm in experiment.arms:
                if arm.get("id") == row.arm_id:
                    return arm
            return {"id": row.arm_id}

    arm = pick_arm(subject_id, experiment.id, experiment.arms)
    if experiment.assignment_scope == "user":
        db.add(
            Assignment(
                subject_type=subject_type,
                subject_id=subject_id,
                experiment_id=experiment.id,
                arm_id=arm["id"],
            )
        )
        await db.flush()
    return arm


async def resolve_scene_version(
    db: AsyncSession,
    world_id: str,
    scene_id: str,
    default_version_id: str,
    user_id: UUID,
    session_id: str,
) -> SceneAssignmentResponse:
    exp = await _find_active_scene_experiment(db, world_id, scene_id)
    if not exp:
        return SceneAssignmentResponse(version_id=default_version_id)

    subject_id = str(user_id) if exp.assignment_scope == "user" else session_id
    subject_type = "user" if exp.assignment_scope == "user" else "session"
    arm = await _get_or_assign_arm(db, exp, subject_type, subject_id)
    version_id = arm.get("version", default_version_id)
    return SceneAssignmentResponse(
        version_id=version_id,
        experiment_id=exp.id,
        arm_id=arm.get("id"),
        assignment_scope=exp.assignment_scope,
    )
