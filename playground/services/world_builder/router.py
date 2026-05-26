"""World builder API routes."""

from pathlib import Path

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from playground.config import get_settings
from playground.deps import CurrentUser, DbSession, OptionalUser, get_return_code
from playground.schemas.world import SceneResolved, TransitionRequest, TransitionResponse, WorldSummary
from playground.services.world_builder.render import render_scene_page
from playground.services.world_builder.service import (
    list_worlds,
    load_world_yaml,
    resolve_scene,
    resolve_scene_guest,
    transition,
)

router = APIRouter(prefix="/worlds", tags=["worlds"])
settings = get_settings()


@router.get("/characters/{character_id}/{asset_path:path}")
async def character_asset(
    character_id: str,
    asset_path: str,
) -> FileResponse:
    """Serve shared character art from worlds_content/characters/<id>/."""
    base = (settings.worlds_content_dir / "characters" / character_id).resolve()
    resolved = (base / asset_path).resolve()
    if not str(resolved).startswith(str(base)):
        raise HTTPException(status_code=404, detail="asset not found")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="asset not found")
    return FileResponse(resolved)


@router.get("/{world_id}/scenes/{scene_id}/assets/{asset_path:path}")
async def scene_asset(
    world_id: str,
    scene_id: str,
    asset_path: str,
) -> FileResponse:
    """Serve static assets for a scene (images, SVG, etc.)."""
    base = settings.worlds_content_dir / world_id / "scenes" / scene_id / "assets"
    resolved = (base / asset_path).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise HTTPException(status_code=404, detail="asset not found")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="asset not found")
    return FileResponse(resolved)


@router.get("", response_model=list[WorldSummary])
async def get_worlds(db: DbSession) -> list[WorldSummary]:
    return await list_worlds(db)


@router.get("/{world_id}/scenes/{scene_id}", response_model=SceneResolved)
async def get_scene(
    db: DbSession,
    world_id: str,
    scene_id: str,
    user: CurrentUser,
    session_id: str | None = Query(None),
    x_session_world: str | None = Header(None, alias="X-Session-World"),
) -> SceneResolved:
    resolved = await resolve_scene(
        db, world_id, scene_id, user.id, session_id, x_session_world
    )
    await db.commit()
    return resolved


@router.get("/{world_id}/scenes/{scene_id}/view", response_class=HTMLResponse)
async def view_scene(
    db: DbSession,
    world_id: str,
    scene_id: str,
    user: OptionalUser = None,
    session_id: str | None = Query(None),
    return_code: Annotated[str | None, Depends(get_return_code)] = None,
    force_version: str | None = Query(
        None,
        description="Dev/admin override: render a specific version instead of the assigned one.",
    ),
    x_session_world: str | None = Header(None, alias="X-Session-World"),
) -> HTMLResponse:
    wy = load_world_yaml(world_id)
    public_scenes = set(wy.get("public_scenes") or [])
    if user is None:
        if scene_id not in public_scenes and force_version is None:
            return RedirectResponse(
                url="/worlds/intro_world/scenes/lab/view",
                status_code=302,
            )
        resolved = await resolve_scene_guest(world_id, scene_id, force_version)
    else:
        resolved = await resolve_scene(
            db,
            world_id,
            scene_id,
            user.id,
            session_id,
            x_session_world,
            force_version=force_version,
        )
        await db.commit()
    response = HTMLResponse(content=render_scene_page(resolved))
    if return_code:
        response.set_cookie(
            key=settings.return_code_cookie,
            value=return_code,
            max_age=settings.return_code_max_age_days * 86400,
            httponly=True,
            samesite="lax",
        )
    return response


@router.post("/{world_id}/scenes/{scene_id}/transition", response_model=TransitionResponse)
async def post_transition(
    db: DbSession,
    world_id: str,
    scene_id: str,
    body: TransitionRequest,
    user: CurrentUser,
) -> TransitionResponse:
    if not body.session_id:
        from fastapi import HTTPException

        raise HTTPException(400, "session_id required")
    result = await transition(
        db, world_id, scene_id, body.event, user.id, body.session_id
    )
    await db.commit()
    return result
