"""World / scene / version catalog for admin UI."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from playground.services.world_builder.service import (
    list_scene_versions,
    list_scenes_for_world,
    list_worlds,
)


async def build_world_catalog(db: AsyncSession) -> list[dict]:
    """Worlds with nested scenes and version ids (from disk)."""
    worlds = await list_worlds(db)
    out: list[dict] = []
    for w in worlds:
        scenes: list[dict] = []
        for scene_id in list_scenes_for_world(w.id):
            versions = list_scene_versions(w.id, scene_id)
            scenes.append(
                {
                    "id": scene_id,
                    "versions": versions,
                    "has_variants": len(versions) > 1,
                }
            )
        out.append(
            {
                "id": w.id,
                "name": w.name or w.id,
                "default_scene_id": w.default_scene_id,
                "scenes": scenes,
                "scene_count": len(scenes),
            }
        )
    return out


async def get_world_detail(db: AsyncSession, world_id: str) -> dict | None:
    catalog = await build_world_catalog(db)
    for w in catalog:
        if w["id"] == world_id:
            return w
    return None
