"""Event list/export filters for the admin dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy import Select, String, func, select
from sqlalchemy.sql import ColumnElement

from playground.models.event import Event


@dataclass
class EventFilters:
    """Query parameters for filtering the events table."""

    date_start: date | None = None
    date_end: date | None = None
    world_id: str | None = None
    scene_id: str | None = None
    scene_version_id: str | None = None
    event_type: str | None = None
    experiment_id: str | None = None
    arm_id: str | None = None
    user_id: UUID | None = None
    session_id: str | None = None

    def active(self) -> bool:
        return any(
            (
                self.date_start,
                self.date_end,
                self.world_id,
                self.scene_id,
                self.scene_version_id,
                self.event_type,
                self.experiment_id,
                self.arm_id,
                self.user_id,
                self.session_id,
            )
        )

    def to_query_params(self) -> dict[str, str]:
        """Build query string values for form repopulation and export links."""
        out: dict[str, str] = {}
        if self.date_start:
            out["date_start"] = self.date_start.isoformat()
        if self.date_end:
            out["date_end"] = self.date_end.isoformat()
        for key in (
            "world_id",
            "scene_id",
            "scene_version_id",
            "event_type",
            "experiment_id",
            "arm_id",
            "user_id",
            "session_id",
        ):
            val = getattr(self, key)
            if val:
                out[key] = str(val)
        return out


def _start_of_day(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _end_of_day_exclusive(d: date) -> datetime:
    """Upper bound (exclusive) for filtering through end of ``d`` UTC."""
    from datetime import timedelta

    return datetime.combine(d, time.max, tzinfo=timezone.utc) + timedelta(
        microseconds=1
    )


def apply_event_filters(
    stmt: Select[tuple[Event]], filters: EventFilters
) -> Select[tuple[Event]]:
    if filters.date_start:
        stmt = stmt.where(Event.ts_server >= _start_of_day(filters.date_start))
    if filters.date_end:
        stmt = stmt.where(Event.ts_server < _end_of_day_exclusive(filters.date_end))
    if filters.world_id:
        stmt = stmt.where(Event.world_id == filters.world_id)
    if filters.scene_id:
        stmt = stmt.where(Event.scene_id == filters.scene_id)
    if filters.scene_version_id:
        stmt = stmt.where(Event.scene_version_id == filters.scene_version_id)
    if filters.event_type:
        stmt = stmt.where(Event.event_type == filters.event_type)
    if filters.user_id:
        stmt = stmt.where(Event.user_id == filters.user_id)
    if filters.session_id:
        stmt = stmt.where(Event.session_id == filters.session_id)
    if filters.experiment_id:
        stmt = _where_experiment(stmt, filters.experiment_id, filters.arm_id)
    elif filters.arm_id:
        stmt = _where_arm_any(stmt, filters.arm_id)
    return stmt


def _json_path(*parts: str) -> str:
    """SQLite JSON path with quoted object keys."""
    return "$" + "".join(f'."{p}"' if p else "" for p in parts)


def _where_experiment(
    stmt: Select[tuple[Event]], experiment_id: str, arm_id: str | None
) -> Select[tuple[Event]]:
    stmt = stmt.where(Event.experiment_arms.isnot(None))
    if arm_id:
        path = _json_path(experiment_id, "arm_id")
        return stmt.where(func.json_extract(Event.experiment_arms, path) == arm_id)
    path = _json_path(experiment_id)
    return stmt.where(func.json_extract(Event.experiment_arms, path).isnot(None))


def _where_arm_any(stmt: Select[tuple[Event]], arm_id: str) -> Select[tuple[Event]]:
    """Match arm_id inside any experiment snapshot (experiment filter not set)."""
    # experiment_arms shape: {"exp_id": {"arm_id": "sky", ...}, ...}
    needle = f'"arm_id": "{arm_id}"'
    col: ColumnElement[str] = func.cast(Event.experiment_arms, String)
    return stmt.where(Event.experiment_arms.isnot(None)).where(col.like(f"%{needle}%"))
