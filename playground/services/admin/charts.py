"""Daily time-series helpers for admin charts (Chart.js)."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.event import Event
from playground.models.user import User
from playground.services.admin.event_filters import EventFilters, apply_event_filters

CHART_DAYS = 30


def _day_range(days: int = CHART_DAYS) -> list[date]:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    return [start + timedelta(days=i) for i in range(days)]


def daily_series_json(labels: list[date], counts: dict[date | str, int]) -> str:
    """Serialize labels + counts for Chart.js."""
    data = [counts.get(d, counts.get(str(d), 0)) for d in labels]
    return json.dumps(
        {
            "labels": [d.isoformat() for d in labels],
            "values": data,
        }
    )


async def daily_new_users(db: AsyncSession, days: int = CHART_DAYS) -> str:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(func.date(User.created_at), func.count())
        .where(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    raw = {row[0]: row[1] for row in result.all()}
    counts: dict[date, int] = {}
    for k, v in raw.items():
        if isinstance(k, str):
            counts[date.fromisoformat(k)] = v
        else:
            counts[k] = v
    return daily_series_json(_day_range(days), counts)


async def daily_events(
    db: AsyncSession,
    *,
    days: int = CHART_DAYS,
    event_type: str | None = None,
    table_filters: EventFilters | None = None,
) -> str:
    """Daily event counts; optional type + same world/scene filters as table."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = (
        select(func.date(Event.ts_server), func.count())
        .where(Event.ts_server >= since)
        .group_by(func.date(Event.ts_server))
        .order_by(func.date(Event.ts_server))
    )
    chart_filters = EventFilters()
    if table_filters:
        chart_filters.date_start = table_filters.date_start
        chart_filters.date_end = table_filters.date_end
        chart_filters.world_id = table_filters.world_id
        chart_filters.scene_id = table_filters.scene_id
        chart_filters.scene_version_id = table_filters.scene_version_id
        chart_filters.experiment_id = table_filters.experiment_id
        chart_filters.arm_id = table_filters.arm_id
        chart_filters.user_id = table_filters.user_id
        chart_filters.session_id = table_filters.session_id
    if event_type:
        chart_filters.event_type = event_type
    q = apply_event_filters(q, chart_filters)
    result = await db.execute(q)
    raw = {row[0]: row[1] for row in result.all()}
    counts: dict[date, int] = {}
    for k, v in raw.items():
        if isinstance(k, str):
            counts[date.fromisoformat(k)] = v
        else:
            counts[k] = v
    return daily_series_json(_day_range(days), counts)
