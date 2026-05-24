# Service: admin

## What this service does

Jinja-rendered admin dashboard: overview, events list (with CSV export and trend chart), users list (with state drill-down), experiments CRUD and lifecycle actions, worlds catalog with per-scene/version previews. All routes are gated by `verify_admin` (optional basic auth, off in dev).

## Key files

Routing and HTTP layer:

- [`playground/services/admin/router.py`](../../playground/services/admin/router.py) — all `/admin/*` routes; defines the `format_dt` / `format_dt_local` Jinja filters.
- [`playground/services/admin/auth.py`](../../playground/services/admin/auth.py) — `verify_admin`. Disabled when `settings.admin_auth_enabled` is false.

Templates ([`playground/services/admin/templates/`](../../playground/services/admin/templates/)):

- `base.html`, `overview.html`, `events.html`, `users.html`, `user_state.html`, `experiments_list.html`, `experiment_form.html`, `experiment_detail.html`, `worlds.html`, `world_detail.html`, `_pagination.html`, `_daily_chart.html`.

Data and helpers:

- [`playground/services/admin/service.py`](../../playground/services/admin/service.py) — query helpers (`overview_stats`, `list_events`, `list_users`, `list_experiments`, `event_filter_options`, etc.), plus `experiment_arm_label` / `payload_preview`.
- [`playground/services/admin/charts.py`](../../playground/services/admin/charts.py) — `daily_events`, `daily_new_users` for Chart.js.
- [`playground/services/admin/pagination.py`](../../playground/services/admin/pagination.py) — generic `Pagination.build(...)`.
- [`playground/services/admin/event_filters.py`](../../playground/services/admin/event_filters.py), [`user_filters.py`](../../playground/services/admin/user_filters.py), [`experiment_filters.py`](../../playground/services/admin/experiment_filters.py) — per-resource filter dataclasses with `to_query_params()` and `apply_*_filters(stmt, f)` builders.
- [`playground/services/admin/world_catalog.py`](../../playground/services/admin/world_catalog.py) — `build_world_catalog`, `get_world_detail` (worlds → scenes → versions).
- [`playground/services/admin/experiment_catalog.py`](../../playground/services/admin/experiment_catalog.py) — nested catalog for the experiment-form cascading dropdowns.
- [`playground/services/admin/experiment_admin.py`](../../playground/services/admin/experiment_admin.py) — see [`ai_docs/services/ab_testing.md`](ab_testing.md).

## Cookbook

### Add a new admin list page

1. Add a filter dataclass under `services/admin/<resource>_filters.py` with `to_query_params()` and an `apply_<resource>_filters(stmt, f)` function.
2. Add query helpers in `services/admin/service.py`: `count_<r>`, `list_<r>`, optionally `<r>_filter_options`.
3. Add the Jinja template under `templates/<r>.html`, extending `base.html`; reuse `_pagination.html`.
4. Add the route in `services/admin/router.py`; build `Pagination` from `count_<r>` + `list_<r>`.

### Add a new admin chart

1. Add a query in `services/admin/charts.py` returning a JSON-serializable structure.
2. Reuse `_daily_chart.html` if it fits; otherwise add a partial.
3. Pass `chart_json = json.dumps(...)` into the template context.

### Preview a scene version as admin (no telemetry)

`GET /admin/worlds/{world_id}/scenes/{scene_id}/preview?version=<id>` calls `resolve_scene_guest` and `render_scene_page(resolved, preview_mode=True)`. The yellow preview banner appears; events are dropped both client-side and server-side.

The world cards at `/admin/worlds` link to `/admin/worlds/<id>` (details, all scenes + versions, individual preview buttons) and to a default-scene preview.

### Experiment lifecycle from the UI

| Route | Action |
|---|---|
| `GET /admin/experiments` | List with state / assignment_scope / world filters; runs `sync_expired_experiments` on load. |
| `GET /admin/experiments/new` | Form with cascading world → scene → version dropdowns; minimum two arms. |
| `POST /admin/experiments` | Create. `name` slugifies to `id` if `id` blank. |
| `GET /admin/experiments/{id}` | Detail: header, schedule, arms + counts, audit log, state actions, extend form. |
| `POST /admin/experiments/{id}/state` | Set state + optional note. |
| `POST /admin/experiments/{id}/extend` | Add `extra_days` to `ends_at`. |

### Users and erasure

- `GET /admin/users` — paginated list with consent filter and signup chart.
- `GET /admin/users/{uuid}/state` — KV state rows for that user.
- Erasure is via `DELETE /me` (identity router), not admin.

## Reference

### Format filters

`format_dt(dt)` → `"YYYY-MM-DD HH:MM UTC"` (or `"—"`). `format_dt_local(dt)` → `datetime-local` input value in UTC. Registered in `router.py` at import time.

### Routes (current)

```
GET  /admin/                                 overview
GET  /admin/events                           list + chart
GET  /admin/events/export                    CSV
GET  /admin/experiments                      list
GET  /admin/experiments/new                  form
POST /admin/experiments                      create
GET  /admin/experiments/{id}                 detail + history
POST /admin/experiments/{id}/state           set state
POST /admin/experiments/{id}/extend          bump ends_at
GET  /admin/users                            list
GET  /admin/users/{uuid}/state               KV view
GET  /admin/worlds                           card grid
GET  /admin/worlds/{id}                      scenes + versions
GET  /admin/worlds/{id}/scenes/{s}/preview   admin preview (preview_mode=True)
```

## Gotchas

- All admin endpoints depend on `verify_admin`. When `admin_auth_enabled=False` (dev default), it short-circuits to `"dev"` — do not rely on it for any access decision in production data flows.
- The experiments list and detail pages run `sync_expired_experiments` on each load and commit. Don't add another loop that also finishes experiments — duplicate audit rows will result.
- Preview routes must use `resolve_scene_guest` + `preview_mode=True`. Using `resolve_scene` would create real sessions and try to assign A/B arms for the admin viewer.
- Catalog helpers (`world_catalog`, `experiment_catalog`) read from disk via `list_scenes_for_world` / `list_scene_versions`. Adding a scene on disk shows up immediately; no migration is needed.
- Filter dataclasses must implement `to_query_params()` returning only non-empty values, otherwise `Pagination.next_url` produces ugly URLs with empty params.
- Template responses use `templates.TemplateResponse(request, "name.html", {...})` — the request object is the first positional arg in the FastAPI Jinja2Templates API used here.
- The admin shell ([`templates/base.html`](../../playground/services/admin/templates/base.html)) sets the viewport meta and uses Bootstrap 5's responsive grid. New tables and forms should stay inside Bootstrap's grid/utility classes; if a custom layout is unavoidable, follow the **Responsive UI baseline** in [`ai_docs/conventions/coding.md`](../conventions/coding.md). Admins do open the dashboard on phones — do not regress mobile usability.
