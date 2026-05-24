"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from playground.config import get_settings
from playground.db import init_db
from playground.identity.router import router as identity_router
from playground.seed import seed_database
from playground.services.ab_testing.router import router as ab_router
from playground.services.admin.router import router as admin_router
from playground.services.event_tracker.router import router as events_router
from playground.services.player_state.router import router as state_router
from playground.services.world_builder.router import router as worlds_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(identity_router)
app.include_router(events_router)
app.include_router(worlds_router)
app.include_router(ab_router)
app.include_router(state_router)
app.include_router(admin_router)

_static = settings.worlds_content_dir.parent / "static"
if _static.exists():
    app.mount("/static", StaticFiles(directory=str(_static)), name="static")


@app.get("/")
async def root() -> RedirectResponse:
    """Entry point: intro world, lab scene (no login required)."""
    return RedirectResponse(
        url="/worlds/intro_world/scenes/lab/view",
        status_code=302,
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
