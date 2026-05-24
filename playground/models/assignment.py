"""Persisted experiment arm assignments (user-scope)."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from playground.db import Base


class Assignment(Base):
    __tablename__ = "assignments"

    subject_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    subject_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    arm_id: Mapped[str] = mapped_column(String(128))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
