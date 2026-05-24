"""Default schedule fields for experiments (tests, seed, admin)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def experiment_schedule(
    *,
    start_days_ago: int = 1,
    duration_days: int = 30,
) -> tuple[datetime, datetime]:
    """Return ``(starts_at, ends_at)`` in UTC for a typical running experiment."""
    now = datetime.now(timezone.utc)
    return now - timedelta(days=start_days_ago), now + timedelta(days=duration_days)
