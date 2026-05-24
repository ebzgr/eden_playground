"""Scene version patch specs."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from playground.db import Base


class SceneVersion(Base):
    __tablename__ = "scene_versions"

    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id"), primary_key=True
    )
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    patch_spec: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(String(32), default="active")
