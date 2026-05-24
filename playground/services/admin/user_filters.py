"""User list filters for admin."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from sqlalchemy import Select

from playground.models.user import User


@dataclass
class UserFilters:
    date_start: date | None = None
    date_end: date | None = None
    consent_state: str | None = None

    def active(self) -> bool:
        return bool(self.date_start or self.date_end or self.consent_state)

    def to_query_params(self) -> dict[str, str]:
        out: dict[str, str] = {}
        if self.date_start:
            out["date_start"] = self.date_start.isoformat()
        if self.date_end:
            out["date_end"] = self.date_end.isoformat()
        if self.consent_state:
            out["consent_state"] = self.consent_state
        return out


def _start_of_day(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _end_of_day_exclusive(d: date) -> datetime:
    from datetime import timedelta

    return datetime.combine(d, time.max, tzinfo=timezone.utc) + timedelta(microseconds=1)


def apply_user_filters(stmt: Select, filters: UserFilters) -> Select:
    if filters.date_start:
        stmt = stmt.where(User.created_at >= _start_of_day(filters.date_start))
    if filters.date_end:
        stmt = stmt.where(User.created_at < _end_of_day_exclusive(filters.date_end))
    if filters.consent_state:
        stmt = stmt.where(User.consent_state == filters.consent_state)
    return stmt
