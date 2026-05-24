"""World and scene resolution from disk + DB."""

from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.config import get_settings
from playground.identity.service import ensure_session
from playground.models.scene import Scene
from playground.models.world import World
from playground.schemas.world import SceneResolved, TransitionResponse, WorldSummary
from playground.services.ab_testing.service import resolve_scene_version
from playground.services.world_builder.demo_config import load_demo_yaml
from playground.services.world_builder.patcher import discover_versions, resolve_version

settings = get_settings()


def _world_dir(world_id: str) -> Path:
    return settings.worlds_content_dir / world_id


def load_world_yaml(world_id: str) -> dict[str, Any]:
    path = _world_dir(world_id) / "world.yaml"
    if not path.exists():
        raise FileNotFoundError(f"world not found: {world_id}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_scene_files(world_id: str, scene_id: str) -> tuple[str, str, str]:
    base = _world_dir(world_id) / "scenes" / scene_id
    html = (base / "base.html").read_text(encoding="utf-8")
    css = (base / "base.css").read_text(encoding="utf-8")
    js = (base / "base.js").read_text(encoding="utf-8")
    return html, css, js


def default_nav_for_scene(world_yaml: dict, scene_id: str) -> dict[str, str]:
    nav = world_yaml.get("navigation", {})
    edges = nav.get(scene_id, nav.get("default", {}))
    if isinstance(edges, dict):
        return {f"on:{k}" if not k.startswith("on:") else k: v for k, v in edges.items()}
    return {}


async def list_worlds(db: AsyncSession) -> list[WorldSummary]:
    result = await db.execute(select(World))
    worlds = result.scalars().all()
    if worlds:
        return [
            WorldSummary(id=w.id, name=w.name, default_scene_id=w.default_scene_id)
            for w in worlds
        ]
    summaries = []
    root = settings.worlds_content_dir
    if root.exists():
        for d in sorted(root.iterdir()):
            if d.is_dir() and (d / "world.yaml").exists():
                wy = load_world_yaml(d.name)
                summaries.append(
                    WorldSummary(
                        id=d.name,
                        name=wy.get("name", d.name),
                        default_scene_id=wy.get("default_scene", "intro"),
                    )
                )
    return summaries


async def resolve_scene(
    db: AsyncSession,
    world_id: str,
    scene_id: str,
    user_id: UUID,
    session_id: str | None,
    stored_world_id: str | None,
    force_version: str | None = None,
) -> SceneResolved:
    world_yaml = load_world_yaml(world_id)
    sid, created = await ensure_session(
        db, user_id, world_id, session_id, stored_world_id
    )

    scene_result = await db.execute(
        select(Scene).where(Scene.world_id == world_id, Scene.id == scene_id)
    )
    scene_row = scene_result.scalar_one_or_none()
    default_version = (
        scene_row.default_version_id
        if scene_row
        else world_yaml.get("scene_versions", {}).get(scene_id, "base")
    )

    assignment = await resolve_scene_version(
        db, world_id, scene_id, default_version, user_id, sid
    )

    base_html, base_css, base_js = load_scene_files(world_id, scene_id)
    base_nav = default_nav_for_scene(world_yaml, scene_id)
    scene_dir = _world_dir(world_id) / "scenes" / scene_id

    chosen_version = force_version or assignment.version_id
    spec = resolve_version(
        scene_dir, chosen_version, base_html, base_css, base_js, base_nav
    )
    html, css, js = spec.html, spec.css, spec.js
    nav = spec.nav_overrides or base_nav
    version_id = spec.id

    arms = None
    if assignment.experiment_id:
        arms = {
            assignment.experiment_id: {
                "arm_id": assignment.arm_id,
                "assignment_scope": assignment.assignment_scope,
            }
        }

    return SceneResolved(
        world_id=world_id,
        scene_id=scene_id,
        version_id=version_id,
        html=html,
        css=css,
        js=js,
        nav=nav,
        experiment_arms=arms,
        session_id=sid,
        demo_config=load_demo_yaml(world_id, scene_id),
    )


async def resolve_scene_guest(
    world_id: str,
    scene_id: str,
    force_version: str | None = None,
) -> SceneResolved:
    """Load scene content without a user (public entry scenes).

    ``force_version`` lets admins/devs preview a non-default version without
    going through assignment.
    """
    world_yaml = load_world_yaml(world_id)
    base_html, base_css, base_js = load_scene_files(world_id, scene_id)
    base_nav = default_nav_for_scene(world_yaml, scene_id)
    version_id = force_version or "base"
    scene_dir = _world_dir(world_id) / "scenes" / scene_id
    spec = resolve_version(
        scene_dir, version_id, base_html, base_css, base_js, base_nav
    )
    return SceneResolved(
        world_id=world_id,
        scene_id=scene_id,
        version_id=spec.id,
        html=spec.html,
        css=spec.css,
        js=spec.js,
        nav=spec.nav_overrides or base_nav,
        experiment_arms=None,
        session_id=None,
        demo_config=load_demo_yaml(world_id, scene_id),
    )


def list_scenes_for_world(world_id: str) -> list[str]:
    """Scene ids that have base assets on disk."""
    scenes_dir = _world_dir(world_id) / "scenes"
    if not scenes_dir.exists():
        return []
    return sorted(
        d.name
        for d in scenes_dir.iterdir()
        if d.is_dir() and (d / "base.html").exists()
    )


def list_scene_versions(world_id: str, scene_id: str) -> list[str]:
    scene_dir = _world_dir(world_id) / "scenes" / scene_id
    return ["base", *discover_versions(scene_dir)]


async def transition(
    db: AsyncSession,
    world_id: str,
    scene_id: str,
    event: str,
    user_id: UUID,
    session_id: str,
) -> TransitionResponse:
    world_yaml = load_world_yaml(world_id)
    nav = default_nav_for_scene(world_yaml, scene_id)
    key = event if event.startswith("on:") else f"on:{event}"
    default_next = nav.get(key, world_yaml.get("default_scene", scene_id))

    return TransitionResponse(next_scene=default_next)
