"""Return code minting, hashing, user lookup, erasure."""

import secrets
import uuid
from base64 import b32encode

from hashlib import blake2b

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.config import get_settings
from playground.models.assignment import Assignment
from playground.models.consent import Consent
from playground.models.event import Event
from playground.models.player_state import PlayerState
from playground.models.session import Session
from playground.models.user import User

settings = get_settings()


def mint_return_code() -> str:
    """Generate a 128-bit random return code (base32, no padding)."""
    raw = secrets.token_bytes(16)
    return b32encode(raw).decode("ascii").rstrip("=")


def hash_return_code(return_code: str) -> str:
    digest = blake2b(
        return_code.encode("utf-8"),
        salt=settings.server_salt.encode("utf-8")[:16].ljust(16, b"\0"),
        digest_size=32,
    )
    return digest.hexdigest()


async def get_or_create_user(db: AsyncSession, return_code: str | None) -> tuple[User, str, bool]:
    """
    Resolve user from return_code. If missing, mint new code and user.

    Returns (user, return_code, created).
    """
    if return_code:
        user_hash = hash_return_code(return_code)
        result = await db.execute(select(User).where(User.user_id_hash == user_hash))
        user = result.scalar_one_or_none()
        if user:
            return user, return_code, False

    new_code = mint_return_code()
    user_hash = hash_return_code(new_code)
    user = User(user_id_hash=user_hash, consent_state="pending")
    db.add(user)
    await db.flush()
    return user, new_code, True


async def ensure_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    world_id: str,
    session_id: str | None,
    stored_world_id: str | None,
) -> tuple[str, bool]:
    """
    Return (session_id, created_new).

    Reuse session_id when same world; else mint new session row.
    """
    if session_id and stored_world_id == world_id:
        result = await db.execute(select(Session).where(Session.id == session_id))
        if result.scalar_one_or_none():
            return session_id, False

    new_id = str(uuid.uuid4())
    db.add(Session(id=new_id, user_id=user_id, world_id=world_id))
    await db.flush()
    return new_id, True


async def record_consent(db: AsyncSession, user: User, state: str) -> None:
    user.consent_state = state
    db.add(Consent(user_id=user.id, state=state))
    await db.flush()


async def erase_user(db: AsyncSession, return_code: str) -> bool:
    user_hash = hash_return_code(return_code)
    result = await db.execute(select(User).where(User.user_id_hash == user_hash))
    user = result.scalar_one_or_none()
    if not user:
        return False
    uid = user.id
    await db.execute(delete(Event).where(Event.user_id == uid))
    await db.execute(delete(PlayerState).where(PlayerState.user_id == uid))
    await db.execute(delete(Assignment).where(
        Assignment.subject_type == "user",
        Assignment.subject_id == str(uid),
    ))
    await db.execute(delete(Consent).where(Consent.user_id == uid))
    await db.execute(delete(Session).where(Session.user_id == uid))
    await db.execute(delete(User).where(User.id == uid))
    await db.commit()
    return True
