"""Seed DB from worlds_content on startup."""

from pathlib import Path

import yaml
from sqlalchemy import select

from playground.config import get_settings
from playground.db import async_session_factory
from playground.models.experiment import Experiment
from playground.models.scene import Scene
from playground.models.scene_version import SceneVersion
from playground.models.world import World

settings = get_settings()


async def seed_database() -> None:
    async with async_session_factory() as db:
        await _sync_worlds_from_disk(db)
        await _ensure_demo_experiment(db)
        await db.commit()


async def _sync_worlds_from_disk(db) -> None:
    root = settings.worlds_content_dir
    if not root.exists():
        return
    for world_dir in sorted(root.iterdir()):
        if not world_dir.is_dir():
            continue
        wy_path = world_dir / "world.yaml"
        if not wy_path.exists():
            continue
        with wy_path.open(encoding="utf-8") as f:
            wy = yaml.safe_load(f) or {}
        world_id = world_dir.name
        if not await db.get(World, world_id):
            db.add(
                World(
                    id=world_id,
                    name=wy.get("name", world_id),
                    default_scene_id=wy.get("default_scene", "intro"),
                    meta=wy,
                )
            )
        scenes_dir = world_dir / "scenes"
        if not scenes_dir.exists():
            continue
        for scene_dir in sorted(scenes_dir.iterdir()):
            if not scene_dir.is_dir():
                continue
            scene_id = scene_dir.name
            default_version = wy.get("scene_versions", {}).get(scene_id, "base")
            existing_scene = await db.execute(
                select(Scene).where(Scene.world_id == world_id, Scene.id == scene_id)
            )
            if not existing_scene.scalar_one_or_none():
                db.add(
                    Scene(
                        id=scene_id,
                        world_id=world_id,
                        default_version_id=default_version,
                    )
                )
            versions_dir = scene_dir / "versions"
            if versions_dir.exists():
                for entry in versions_dir.iterdir():
                    if not (entry.is_file() and entry.suffix in (".yaml", ".yml")):
                        continue
                    vid = entry.stem
                    manifest: dict = (
                        yaml.safe_load(entry.read_text(encoding="utf-8")) or {}
                    )
                    if not await db.get(SceneVersion, (scene_id, vid)):
                        db.add(
                            SceneVersion(
                                scene_id=scene_id,
                                id=vid,
                                patch_spec=manifest,
                            )
                        )
            if not await db.get(SceneVersion, (scene_id, "base")):
                db.add(
                    SceneVersion(
                        scene_id=scene_id,
                        id="base",
                        patch_spec={},
                    )
                )
        await db.flush()


async def _ensure_demo_experiment(db) -> None:
    from playground.services.ab_testing.defaults import experiment_schedule
    from playground.services.admin.experiment_admin import create_experiment

    exp_id = "exp_deal_intro_v0"
    if await db.get(Experiment, exp_id):
        return
    result = await db.execute(select(Experiment).where(Experiment.state == "live"))
    if result.scalars().first():
        return
    starts_at, ends_at = experiment_schedule(duration_days=90)
    await create_experiment(
        db,
        id=exp_id,
        name="Deal intro — base vs urgent",
        assignment_scope="user",
        world="deal_world",
        scene="intro",
        arms=[
            {"id": "control", "version": "base", "weight": 50},
            {"id": "urgent", "version": "urgent", "weight": 50},
        ],
        explanation=(
            "Compare base vs urgent intro copy on deal_world/intro. "
            "Primary metric: CTA click-through to checkout."
        ),
        starts_at=starts_at,
        ends_at=ends_at,
        state="live",
    )

