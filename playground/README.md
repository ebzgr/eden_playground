# Playground backend (v0)

FastAPI platform for event tracking, world/scene delivery, A/B testing, player state, and admin.

## Database and seed

- Default DB: `/tmp/eden_playground.db` (see `playground/config.py`). Set `DATABASE_URL` to override.
- **Startup:** `uvicorn` runs `init_db()` (Alembic) then `seed_database()` automatically.
- **Explicit init** (migrations + sync worlds from disk + demo experiment if missing):

```bash
python -m playground db-init
```

- **Reset dev DB:** `rm -f /tmp/eden_playground.db*` then `python -m playground db-init`.

Seed reads `playground/worlds_content/*/world.yaml` and scene `versions/*.yaml` into ORM rows; it does not overwrite existing rows.

## Run locally

See the root [README.md](../README.md) for full first-time setup. Short version:

```bash
cd /path/to/eden_playground
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn playground.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin/ (no login by default; set `ADMIN_AUTH_ENABLED=true` and `ADMIN_USERNAME` / `ADMIN_PASSWORD` to require basic auth)
- **Entry (player journey):** http://localhost:8000/ → intro lab → consent → demo → map
- **Map welcome (Gaia):** http://localhost:8000/worlds/map_world/scenes/welcome/view
- **Map scene (orbs):** http://localhost:8000/worlds/map_world/scenes/map/view
- Dev sample: http://localhost:8000/worlds/deal_world/scenes/intro/view

## Tests

With `.venv` activated:

```bash
pytest
```

## Admin UI

The dashboard at `/admin/` uses **Bootstrap 5** and **Chart.js** (CDN — no npm build). Player world scenes are unchanged and can use any styling per scene/version.

List pages (Events, Users, Experiments) share generic server pagination in `playground/services/admin/pagination.py` (`page`, `page_size`, SQL `LIMIT`/`OFFSET`). Each resource has its own filter module (`event_filters`, `user_filters`, `experiment_filters`).

## Services

| Service | Prefix | Role |
|---------|--------|------|
| Identity | `/identity`, `/consent`, `/me` | Return code, consent, erasure |
| Event Tracker | `/events` | Append-only telemetry |
| World Builder | `/worlds` | Scene resolution + transitions |
| A/B Testing | `/assignments` | Scene version arms (scheduled, auditable) |
| Player State | `/state` | Per-user KV (orbs, loyalty, …) |
| Admin | `/admin` | Jinja dashboard |

Set `SERVER_SALT` in production.

**Database:** defaults to `/tmp/eden_playground.db` (SQLite needs a writable directory for WAL files; project mounts on fuseblk often fail). Override with `DATABASE_URL=sqlite+aiosqlite:////path/to/db`. On first run, an existing repo-root `playground.db` is copied into `/tmp` once.

**Migrations:** startup runs `alembic upgrade head` automatically. If you hit schema errors on an old dev DB, either restart the server (legacy DBs are stamped and upgraded) or run `alembic upgrade head` manually.
