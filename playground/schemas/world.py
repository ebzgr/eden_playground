"""World builder schemas."""

from typing import Any

from pydantic import BaseModel


class WorldSummary(BaseModel):
    id: str
    name: str
    default_scene_id: str


class SceneResolved(BaseModel):
    world_id: str
    scene_id: str
    version_id: str
    html: str
    css: str
    js: str
    nav: dict[str, Any]
    experiment_arms: dict[str, Any] | None = None
    session_id: str | None = None
    demo_config: dict[str, Any] | None = None


class TransitionRequest(BaseModel):
    event: str
    session_id: str | None = None


class TransitionResponse(BaseModel):
    next_scene: str
    experiment_id: str | None = None
    arm_id: str | None = None
