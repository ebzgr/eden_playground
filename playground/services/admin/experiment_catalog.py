"""World / scene / version metadata for experiment admin forms."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from playground.services.world_builder.service import (
    list_scene_versions,
    list_scenes_for_world,
    list_worlds,
)


async def build_experiment_catalog(db: AsyncSession) -> dict:
    """Nested catalog for cascading dropdowns in the create form."""
    worlds = await list_worlds(db)
    out: dict[str, dict] = {}
    for w in worlds:
        scenes: dict[str, list[str]] = {}
        for scene_id in list_scenes_for_world(w.id):
            scenes[scene_id] = list_scene_versions(w.id, scene_id)
        out[w.id] = {
            "label": w.name or w.id,
            "default_scene": w.default_scene_id,
            "scenes": scenes,
        }
    return out
