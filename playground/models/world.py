"""World metadata (DB mirror; content lives on disk)."""

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from playground.db import Base


class World(Base):
    __tablename__ = "worlds"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    default_scene_id: Mapped[str] = mapped_column(String(128))
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
