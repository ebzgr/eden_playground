"""A/B testing schemas (scene version only)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SceneAssignmentResponse(BaseModel):
    version_id: str
    experiment_id: str | None = None
    arm_id: str | None = None
    assignment_scope: str | None = None


class ExperimentCreate(BaseModel):
    id: str
    name: str
    assignment_scope: str
    target: dict[str, Any]
    arms: list[dict[str, Any]]
    state: str = "draft"
    starts_at: datetime
    ends_at: datetime
    explanation: str = ""


class ExperimentOut(BaseModel):
    id: str
    name: str
    target_scope: str
    assignment_scope: str
    target: dict[str, Any]
    arms: list[dict[str, Any]]
    state: str
    starts_at: datetime
    ends_at: datetime
    explanation: str

    model_config = {"from_attributes": True}
