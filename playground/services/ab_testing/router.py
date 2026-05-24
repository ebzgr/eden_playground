"""A/B testing API routes (scene version assignment only)."""

from uuid import UUID

from fastapi import APIRouter, Query

from playground.deps import DbSession
from playground.schemas.experiment import SceneAssignmentResponse
from playground.services.ab_testing.service import resolve_scene_version

router = APIRouter(prefix="/assignments", tags=["ab-testing"])


@router.get("/scene/{world_id}/{scene_id}", response_model=SceneAssignmentResponse)
async def get_scene_assignment(
    db: DbSession,
    world_id: str,
    scene_id: str,
    user_id: UUID = Query(...),
    session_id: str = Query(...),
    default_version_id: str = Query("base"),
) -> SceneAssignmentResponse:
    return await resolve_scene_version(
        db, world_id, scene_id, default_version_id, user_id, session_id
    )
