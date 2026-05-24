"""Identity API routes."""

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from playground.config import get_settings
from playground.deps import DbSession, get_return_code
from playground.identity.service import erase_user, get_or_create_user, record_consent

router = APIRouter(tags=["identity"])
settings = get_settings()


class IdentityResponse(BaseModel):
    return_code: str
    user_id: str
    consent_state: str
    created: bool


class ConsentRequest(BaseModel):
    state: str


class ConsentResponse(BaseModel):
    consent_state: str


@router.post("/identity", response_model=IdentityResponse)
async def post_identity(
    db: DbSession,
    response: Response,
    return_code: str | None = Depends(get_return_code),
) -> IdentityResponse:
    user, code, created = await get_or_create_user(db, return_code)
    await db.commit()
    response.set_cookie(
        key=settings.return_code_cookie,
        value=code,
        max_age=settings.return_code_max_age_days * 86400,
        httponly=False,
        samesite="lax",
    )
    return IdentityResponse(
        return_code=code,
        user_id=str(user.id),
        consent_state=user.consent_state,
        created=created,
    )


@router.post("/consent", response_model=ConsentResponse)
async def post_consent(
    db: DbSession,
    body: ConsentRequest,
    return_code: str | None = Depends(get_return_code),
) -> ConsentResponse:
    if body.state not in ("granted", "denied"):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="state must be granted or denied")
    user, _, _ = await get_or_create_user(db, return_code)
    await record_consent(db, user, body.state)
    await db.commit()
    return ConsentResponse(consent_state=body.state)


@router.delete("/me")
async def delete_me(
    db: DbSession,
    return_code: str | None = Depends(get_return_code),
) -> dict:
    if not return_code:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Missing return_code")
    ok = await erase_user(db, return_code)
    if not ok:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True}
