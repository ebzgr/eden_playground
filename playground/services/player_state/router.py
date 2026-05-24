"""Player state API routes."""

from fastapi import APIRouter, Header, Query

from playground.deps import CurrentUser, DbSession
from playground.schemas.player_state import (
    StateAllResponse,
    StatePatchRequest,
    StateValueResponse,
)
from playground.services.player_state.service import get_all_state, get_state, patch_state, set_state

router = APIRouter(prefix="/state", tags=["player-state"])


@router.get("", response_model=StateAllResponse)
async def get_all(
    db: DbSession,
    user: CurrentUser,
) -> StateAllResponse:
    items = await get_all_state(db, user.id)
    return StateAllResponse(items=items)


@router.get("/{key:path}", response_model=StateValueResponse)
async def get_one(
    db: DbSession,
    key: str,
    user: CurrentUser,
) -> StateValueResponse:
    value = await get_state(db, user.id, key)
    return StateValueResponse(key=key, value=value)


@router.post("/{key:path}", response_model=StateValueResponse)
async def post_set(
    db: DbSession,
    key: str,
    body: dict,
    user: CurrentUser,
    session_id: str = Query(...),
    x_world_id: str | None = Header(None, alias="X-World-Id"),
    x_scene_id: str | None = Header(None, alias="X-Scene-Id"),
) -> StateValueResponse:
    value = body.get("value", body)
    result = await set_state(
        db, user, key, value, session_id, x_world_id, x_scene_id
    )
    await db.commit()
    return StateValueResponse(key=key, value=result)


@router.patch("/{key:path}", response_model=StateValueResponse)
async def patch_one(
    db: DbSession,
    key: str,
    body: StatePatchRequest,
    user: CurrentUser,
    session_id: str = Query(...),
    x_world_id: str | None = Header(None, alias="X-World-Id"),
    x_scene_id: str | None = Header(None, alias="X-Scene-Id"),
) -> StateValueResponse:
    result = await patch_state(
        db, user, key, body.op, body.value, session_id, x_world_id, x_scene_id
    )
    await db.commit()
    return StateValueResponse(key=key, value=result)
