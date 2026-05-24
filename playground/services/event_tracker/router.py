"""Event tracker API routes."""

from fastapi import APIRouter, Depends, Header, HTTPException

from playground.deps import CurrentUser, DbSession, get_return_code
from playground.identity.service import get_or_create_user
from playground.schemas.event import EventsIngestRequest, EventsIngestResponse
from playground.services.event_tracker.service import ingest_events

router = APIRouter(tags=["events"])


@router.post("/events", response_model=EventsIngestResponse)
async def post_events(
    db: DbSession,
    body: EventsIngestRequest,
    user: CurrentUser,
    x_playground_preview: str | None = Header(None, alias="X-Playground-Preview"),
) -> EventsIngestResponse:
    if x_playground_preview == "1":
        return EventsIngestResponse(accepted=0)
    if body.session_id and str(body.session_id).startswith("preview-"):
        return EventsIngestResponse(accepted=0)
    accepted = await ingest_events(db, user, body.session_id, body.events)
    await db.commit()
    return EventsIngestResponse(accepted=accepted)
