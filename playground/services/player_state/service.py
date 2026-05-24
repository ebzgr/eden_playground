"""Player state read/write with state_changed event emission."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.models.player_state import PlayerState
from playground.models.user import User
from playground.services.event_tracker.service import emit_state_changed
from playground.services.player_state.ops import apply_op


async def get_all_state(db: AsyncSession, user_id: UUID) -> dict:
    result = await db.execute(
        select(PlayerState).where(PlayerState.user_id == user_id)
    )
    return {row.key: row.value for row in result.scalars().all()}


async def _get_row(db: AsyncSession, user_id: UUID, key: str) -> PlayerState | None:
    result = await db.execute(
        select(PlayerState).where(
            PlayerState.user_id == user_id,
            PlayerState.key == key,
        )
    )
    return result.scalar_one_or_none()


async def get_state(db: AsyncSession, user_id: UUID, key: str) -> object | None:
    row = await _get_row(db, user_id, key)
    return row.value if row else None


async def set_state(
    db: AsyncSession,
    user: User,
    key: str,
    value: object,
    session_id: str,
    world_id: str | None = None,
    scene_id: str | None = None,
) -> object:
    row = await _get_row(db, user.id, key)
    old = row.value if row else None
    if row:
        row.value = value
    else:
        db.add(PlayerState(user_id=user.id, key=key, value=value))
    await db.flush()
    await emit_state_changed(
        db, user, session_id, key, "set", old, value, world_id, scene_id
    )
    return value


async def patch_state(
    db: AsyncSession,
    user: User,
    key: str,
    op: str,
    value: object,
    session_id: str,
    world_id: str | None = None,
    scene_id: str | None = None,
) -> object:
    row = await _get_row(db, user.id, key)
    old = row.value if row else None
    new_value = apply_op(old, op, value)
    if row:
        row.value = new_value
    else:
        db.add(PlayerState(user_id=user.id, key=key, value=new_value))
    await db.flush()
    await emit_state_changed(
        db, user, session_id, key, op, old, new_value, world_id, scene_id
    )
    return new_value
