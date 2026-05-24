"""Admin dashboard routes (Jinja HTML)."""

import csv
import io
import json
from datetime import date, datetime, timezone
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from playground.deps import DbSession
from playground.identity.service import erase_user
from playground.models.experiment import Experiment
from playground.models.user import User
from playground.services.ab_testing.lifecycle import (
    extend_experiment,
    set_experiment_state,
    sync_expired_experiments,
)
from playground.services.admin.auth import verify_admin
from playground.services.admin.experiment_admin import (
    create_experiment,
    default_schedule,
    get_experiment_detail_context,
    parse_admin_datetime,
    parse_arms_from_form,
    resolve_experiment_id,
)
from playground.services.admin.experiment_catalog import build_experiment_catalog
from playground.services.admin.world_catalog import build_world_catalog, get_world_detail
from playground.services.world_builder.render import render_scene_page
from playground.services.world_builder.service import resolve_scene_guest
from playground.services.admin.charts import daily_events, daily_new_users
from playground.services.admin.event_filters import EventFilters
from playground.services.admin.experiment_filters import ExperimentFilters
from playground.services.admin.pagination import (
    DEFAULT_PAGE_SIZE,
    Pagination,
)
from playground.services.admin.service import (
    count_events,
    count_experiments,
    count_users,
    event_filter_options,
    experiment_arm_counts,
    experiment_filter_options,
    experiment_arm_label,
    list_events,
    list_experiments,
    list_users,
    overview_stats,
    payload_preview,
    user_filter_options,
    user_state_rows,
)
from playground.services.admin.user_filters import UserFilters

from pathlib import Path

router = APIRouter(prefix="/admin", tags=["admin"])
_templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.strftime("%Y-%m-%d %H:%M UTC")


def _format_dt_local(value: datetime | None) -> str:
    """``datetime-local`` input value (UTC, no offset suffix)."""
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.strftime("%Y-%m-%dT%H:%M")


templates.env.filters["format_dt"] = _format_dt
templates.env.filters["format_dt_local"] = _format_dt_local

HISTORY_ACTION_LABELS = {
    "created": "Created",
    "live": "Went live",
    "paused": "Paused",
    "finished": "Finished",
    "extended": "Extended",
    "draft": "Set to draft",
    "status_change": "Status changed",
}


@router.get("/", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    db: DbSession,
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    stats = await overview_stats(db)
    return templates.TemplateResponse(
        request, "overview.html", {"stats": stats}
    )


def _parse_event_filters(
    date_start: date | None = None,
    date_end: date | None = None,
    world_id: str | None = None,
    scene_id: str | None = None,
    scene_version_id: str | None = None,
    event_type: str | None = None,
    experiment_id: str | None = None,
    arm_id: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> EventFilters:
    uid: UUID | None = None
    if user_id:
        try:
            uid = UUID(user_id.strip())
        except ValueError:
            uid = None
    return EventFilters(
        date_start=date_start,
        date_end=date_end,
        world_id=world_id or None,
        scene_id=scene_id or None,
        scene_version_id=scene_version_id or None,
        event_type=event_type or None,
        experiment_id=experiment_id or None,
        arm_id=arm_id or None,
        user_id=uid,
        session_id=session_id or None,
    )


@router.get("/events", response_class=HTMLResponse)
async def admin_events(
    request: Request,
    db: DbSession,
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    world_id: str | None = Query(None),
    scene_id: str | None = Query(None),
    scene_version_id: str | None = Query(None),
    event_type: str | None = Query(None),
    experiment_id: str | None = Query(None),
    arm_id: str | None = Query(None),
    user_id: str | None = Query(None),
    session_id: str | None = Query(None),
    trend_event_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    filters = _parse_event_filters(
        date_start=date_start,
        date_end=date_end,
        world_id=world_id,
        scene_id=scene_id,
        scene_version_id=scene_version_id,
        event_type=event_type,
        experiment_id=experiment_id,
        arm_id=arm_id,
        user_id=user_id,
        session_id=session_id,
    )
    export_limit = 10_000
    total = await count_events(db, filters)
    qp = filters.to_query_params()
    if trend_event_type:
        qp["trend_event_type"] = trend_event_type
    pag = Pagination.build(
        total=total,
        page=page,
        page_size=page_size,
        base_path="/admin/events",
        query_params=qp,
    )
    events = await list_events(
        db, filters, limit=pag.page_size, offset=pag.offset
    )
    options = await event_filter_options(db)
    export_url = "/admin/events/export"
    if filters.to_query_params():
        export_url += "?" + urlencode(filters.to_query_params())
    chart_json = await daily_events(
        db,
        event_type=trend_event_type or None,
        table_filters=filters,
    )
    chart_label = trend_event_type or "All event types"
    return templates.TemplateResponse(
        request,
        "events.html",
        {
            "events": events,
            "filters": filters,
            "filter_options": options,
            "scene_pairs_json": json.dumps(options["scene_pairs"]),
            "experiments_json": json.dumps(options["experiments"]),
            "pagination": pag,
            "export_limit": export_limit,
            "export_url": export_url,
            "trend_event_type": trend_event_type or "",
            "chart_json": chart_json,
            "chart_label": chart_label,
            "experiment_arm_label": experiment_arm_label,
            "payload_preview": payload_preview,
        },
    )


@router.get("/events/export")
async def export_events_csv(
    db: DbSession,
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    world_id: str | None = Query(None),
    scene_id: str | None = Query(None),
    scene_version_id: str | None = Query(None),
    event_type: str | None = Query(None),
    experiment_id: str | None = Query(None),
    arm_id: str | None = Query(None),
    user_id: str | None = Query(None),
    session_id: str | None = Query(None),
    _: str = Depends(verify_admin),
) -> StreamingResponse:
    filters = _parse_event_filters(
        date_start=date_start,
        date_end=date_end,
        world_id=world_id,
        scene_id=scene_id,
        scene_version_id=scene_version_id,
        event_type=event_type,
        experiment_id=experiment_id,
        arm_id=arm_id,
        user_id=user_id,
        session_id=session_id,
    )
    events = await list_events(db, filters, limit=10_000)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "user_id",
            "session_id",
            "world_id",
            "scene_id",
            "scene_version_id",
            "event_type",
            "experiment_arms",
            "payload",
            "ts_client",
            "ts_server",
        ]
    )
    for e in events:
        writer.writerow(
            [
                e.id,
                e.user_id,
                e.session_id,
                e.world_id or "",
                e.scene_id or "",
                e.scene_version_id or "",
                e.event_type,
                experiment_arm_label(e.experiment_arms),
                json.dumps(e.payload, ensure_ascii=False)
                if e.payload is not None
                else "",
                e.ts_client.isoformat() if e.ts_client else "",
                e.ts_server.isoformat() if e.ts_server else "",
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=events.csv"},
    )


def _parse_experiment_filters(
    state: str | None = None,
    assignment_scope: str | None = None,
    world_id: str | None = None,
) -> ExperimentFilters:
    return ExperimentFilters(
        state=state or None,
        assignment_scope=assignment_scope or None,
        world_id=world_id or None,
    )


def _parse_user_filters(
    date_start: date | None = None,
    date_end: date | None = None,
    consent_state: str | None = None,
) -> UserFilters:
    return UserFilters(
        date_start=date_start,
        date_end=date_end,
        consent_state=consent_state or None,
    )


@router.get("/experiments", response_class=HTMLResponse)
async def admin_experiments_list(
    request: Request,
    db: DbSession,
    state: str | None = Query(None),
    assignment_scope: str | None = Query(None),
    world_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    await sync_expired_experiments(db)
    await db.commit()
    filters = _parse_experiment_filters(
        state=state,
        assignment_scope=assignment_scope,
        world_id=world_id,
    )
    total = await count_experiments(db, filters)
    pag = Pagination.build(
        total=total,
        page=page,
        page_size=page_size,
        base_path="/admin/experiments",
        query_params=filters.to_query_params(),
    )
    exps = await list_experiments(
        db, filters, limit=pag.page_size, offset=pag.offset
    )
    options = await experiment_filter_options(db)
    return templates.TemplateResponse(
        request,
        "experiments_list.html",
        {
            "experiments": exps,
            "filters": filters,
            "filter_options": options,
            "pagination": pag,
        },
    )


@router.get("/experiments/new", response_class=HTMLResponse)
async def admin_experiment_new(
    request: Request,
    db: DbSession,
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    starts, ends = default_schedule()
    catalog = await build_experiment_catalog(db)
    return templates.TemplateResponse(
        request,
        "experiment_form.html",
        {
            "experiment": None,
            "default_starts": starts,
            "default_ends": ends,
            "catalog_json": json.dumps(catalog),
        },
    )


@router.post("/experiments")
async def admin_experiment_create(
    db: DbSession,
    name: str = Form(...),
    id: str = Form(""),
    assignment_scope: str = Form(...),
    world: str = Form(...),
    scene: str = Form(...),
    explanation: str = Form(""),
    starts_at: str = Form(...),
    ends_at: str = Form(...),
    arm_id: list[str] = Form(default=[]),
    arm_version: list[str] = Form(default=[]),
    arm_weight: list[int] = Form(default=[]),
    state: str = Form("draft"),
    _: str = Depends(verify_admin),
) -> RedirectResponse:
    try:
        exp_id = resolve_experiment_id(name, id)
        arms = parse_arms_from_form(arm_id, arm_version, arm_weight)
        await create_experiment(
            db,
            id=exp_id,
            name=name,
            assignment_scope=assignment_scope,
            world=world.strip(),
            scene=scene.strip(),
            arms=arms,
            explanation=explanation,
            starts_at=parse_admin_datetime(starts_at),
            ends_at=parse_admin_datetime(ends_at),
            state=state,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url=f"/admin/experiments/{exp_id}", status_code=303)


@router.get("/experiments/{exp_id}", response_class=HTMLResponse)
async def admin_experiment_detail(
    request: Request,
    db: DbSession,
    exp_id: str,
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    ctx = await get_experiment_detail_context(db, exp_id)
    if not ctx:
        return templates.TemplateResponse(
            request,
            "experiment_detail.html",
            {"experiment": None, "arm_counts": {}, "history": []},
        )
    await db.commit()
    exp = ctx["experiment"]
    counts = await experiment_arm_counts(db, exp_id)
    return templates.TemplateResponse(
        request,
        "experiment_detail.html",
        {
            "experiment": exp,
            "arm_counts": counts,
            "history": ctx["history"],
            "history_action_labels": HISTORY_ACTION_LABELS,
        },
    )


@router.post("/experiments/{exp_id}/state")
async def admin_experiment_set_state(
    db: DbSession,
    exp_id: str,
    new_state: str = Form(...),
    note: str = Form(""),
    _: str = Depends(verify_admin),
) -> RedirectResponse:
    exp = await db.get(Experiment, exp_id)
    if exp:
        await sync_expired_experiments(db)
        await set_experiment_state(
            db, exp, new_state, note=note.strip() or None
        )
        await db.commit()
    return RedirectResponse(url=f"/admin/experiments/{exp_id}", status_code=303)


@router.post("/experiments/{exp_id}/extend")
async def admin_experiment_extend(
    db: DbSession,
    exp_id: str,
    extra_days: int = Form(...),
    note: str = Form(""),
    _: str = Depends(verify_admin),
) -> RedirectResponse:
    exp = await db.get(Experiment, exp_id)
    if exp:
        try:
            await extend_experiment(
                db, exp, extra_days, note=note.strip() or None
            )
            await db.commit()
        except ValueError:
            pass
    return RedirectResponse(url=f"/admin/experiments/{exp_id}", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    db: DbSession,
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    consent_state: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    filters = _parse_user_filters(
        date_start=date_start,
        date_end=date_end,
        consent_state=consent_state,
    )
    total = await count_users(db, filters)
    pag = Pagination.build(
        total=total,
        page=page,
        page_size=page_size,
        base_path="/admin/users",
        query_params=filters.to_query_params(),
    )
    users = await list_users(db, filters, limit=pag.page_size, offset=pag.offset)
    options = await user_filter_options(db)
    chart_json = await daily_new_users(db)
    return templates.TemplateResponse(
        request,
        "users.html",
        {
            "users": users,
            "filters": filters,
            "filter_options": options,
            "pagination": pag,
            "chart_json": chart_json,
        },
    )


@router.get("/users/{user_id}/state", response_class=HTMLResponse)
async def admin_user_state(
    request: Request,
    db: DbSession,
    user_id: UUID,
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    rows = await user_state_rows(db, user_id)
    user = await db.get(User, user_id)
    return templates.TemplateResponse(
        request,
        "user_state.html",
        {"user": user, "rows": rows},
    )


@router.get("/worlds", response_class=HTMLResponse)
async def admin_worlds(
    request: Request,
    db: DbSession,
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    worlds = await build_world_catalog(db)
    return templates.TemplateResponse(request, "worlds.html", {"worlds": worlds})


@router.get("/worlds/{world_id}", response_class=HTMLResponse)
async def admin_world_detail(
    request: Request,
    db: DbSession,
    world_id: str,
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    world = await get_world_detail(db, world_id)
    if not world:
        return templates.TemplateResponse(
            request,
            "world_detail.html",
            {"world": None},
        )
    return templates.TemplateResponse(
        request,
        "world_detail.html",
        {"world": world},
    )


@router.get("/worlds/{world_id}/scenes/{scene_id}/preview", response_class=HTMLResponse)
async def admin_scene_preview(
    world_id: str,
    scene_id: str,
    version: str = Query("base"),
    _: str = Depends(verify_admin),
) -> HTMLResponse:
    """Admin-only preview — no events, consent, or assignment persistence."""
    resolved = await resolve_scene_guest(world_id, scene_id, force_version=version)
    return HTMLResponse(content=render_scene_page(resolved, preview_mode=True))
