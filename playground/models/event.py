"""Append-only event log."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from playground.db import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_ts_server", "ts_server"),
        Index("ix_events_world_id", "world_id"),
        Index("ix_events_scene_id", "scene_id"),
        Index("ix_events_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    world_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scene_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scene_version_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    experiment_arms: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    event_type: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    ts_client: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ts_server: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
