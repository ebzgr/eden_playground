"""Scene metadata."""

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from playground.db import Base


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("worlds.id"), index=True)
    default_version_id: Mapped[str] = mapped_column(String(128))
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
