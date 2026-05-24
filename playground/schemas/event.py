"""Event tracker schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventItem(BaseModel):
    event_type: str
    payload: dict[str, Any] | list[Any] | None = None
    world_id: str | None = None
    scene_id: str | None = None
    scene_version_id: str | None = None
    experiment_arms: dict[str, Any] | list[Any] | None = None
    ts_client: datetime | None = None


class EventsIngestRequest(BaseModel):
    session_id: str
    events: list[EventItem] = Field(default_factory=list)


class EventsIngestResponse(BaseModel):
    accepted: int
