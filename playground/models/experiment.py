"""A/B experiment definitions (scene version only)."""

from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from playground.db import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    # Kept for schema compatibility; always ``scene_version`` for new experiments.
    target_scope: Mapped[str] = mapped_column(String(32), default="scene_version")
    assignment_scope: Mapped[str] = mapped_column(String(32))
    target: Mapped[dict] = mapped_column(JSON)
    arms: Mapped[list] = mapped_column(JSON)
    guardrails: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    state: Mapped[str] = mapped_column(String(32), default="draft")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
