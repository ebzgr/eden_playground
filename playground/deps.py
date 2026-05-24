"""FastAPI dependencies shared across services."""

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playground.config import get_settings
from playground.db import get_db
from playground.identity.service import hash_return_code
from playground.models.user import User

_settings = get_settings()
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_return_code(
    return_code: Annotated[
        str | None, Cookie(alias=_settings.return_code_cookie)
    ] = None,
    x_return_code: Annotated[str | None, Header(alias="X-Return-Code")] = None,
) -> str | None:
    """Return code from cookie or header (for API clients and tests)."""
    return return_code or x_return_code


async def get_current_user(
    db: DbSession,
    return_code: Annotated[str | None, Depends(get_return_code)] = None,
) -> User:
    if not return_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing return_code (cookie or X-Return-Code header)",
        )
    user_hash = hash_return_code(return_code)
    result = await db.execute(select(User).where(User.user_id_hash == user_hash))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown return_code",
        )
    return user


async def get_optional_user(
    db: DbSession,
    return_code: Annotated[str | None, Depends(get_return_code)] = None,
) -> User | None:
    if not return_code:
        return None
    user_hash = hash_return_code(return_code)
    result = await db.execute(select(User).where(User.user_id_hash == user_hash))
    return result.scalar_one_or_none()


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_user_id_param(user_id: UUID) -> UUID:
    return user_id
