"""Event ingestion logic."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.event import Event
from playground.models.user import User
from playground.schemas.event import EventItem
from playground.services.event_tracker.privacy import consent_allows_tracking


async def ingest_events(
    db: AsyncSession,
    user: User,
    session_id: str,
    items: list[EventItem],
) -> int:
    if not consent_allows_tracking(user):
        return 0
    count = 0
    now = datetime.now(timezone.utc)
    for item in items:
        db.add(
            Event(
                user_id=user.id,
                session_id=session_id,
                world_id=item.world_id,
                scene_id=item.scene_id,
                scene_version_id=item.scene_version_id,
                experiment_arms=item.experiment_arms,
                event_type=item.event_type,
                payload=item.payload,
                ts_client=item.ts_client,
                ts_server=now,
            )
        )
        count += 1
    await db.flush()
    return count


async def emit_state_changed(
    db: AsyncSession,
    user: User,
    session_id: str,
    key: str,
    op: str,
    old_value: object,
    new_value: object,
    world_id: str | None = None,
    scene_id: str | None = None,
) -> None:
    """Append a state_changed event (caller must have verified consent)."""
    if not consent_allows_tracking(user):
        return
    db.add(
        Event(
            user_id=user.id,
            session_id=session_id,
            world_id=world_id,
            scene_id=scene_id,
            event_type="state_changed",
            payload={
                "key": key,
                "op": op,
                "old_value": old_value,
                "new_value": new_value,
            },
            ts_server=datetime.now(timezone.utc),
        )
    )
    await db.flush()
