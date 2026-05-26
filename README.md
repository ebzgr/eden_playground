# eden_playground

**eden_playground** is a small static website for **Marketing for Betterment's playground**: a research + awareness platform that makes manipulative marketing techniques more visible through immersive, art-driven “worlds”, and documents the conceptual, ethical, and methodology layers behind that work.

## What’s in this repo

- `docs/`: the site (static HTML/CSS/JS) and its wiki-style navigation.
- `playground/`: **v0 backend** (FastAPI) — event tracker, world builder, A/B testing, player state, admin dashboard, **Demo SDK** (`demo.yaml` scroll-scrubbed scenes).
- `Documents/`: reference PDFs used by the project.

## Getting started (platform API)

**Requirements:** Python 3.12+

Each collaborator creates their own virtual environment locally. `.venv/` is gitignored and is not committed.

### First-time setup

From the repository root:

```bash
cd /path/to/eden_playground
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

If `python3 -m venv .venv` or `pip install` fails (for example on a network-mounted project directory), create the venv on a local filesystem instead:

```bash
python3 -m venv /tmp/eden_pg_venv
source /tmp/eden_pg_venv/bin/activate
pip install -e ".[dev]"
```

### Database and seed

The dev SQLite database defaults to **`/tmp/eden_playground.db`** (writable on network-mounted project trees). Override with `DATABASE_URL` if needed.

On **first run**, the app applies Alembic migrations and seeds data from `playground/worlds_content/` (worlds, scenes, version rows) plus a demo A/B experiment when none is live. You do not need a separate seed step if you start the server — but you can initialize explicitly:

```bash
source .venv/bin/activate
python -m playground db-init
```

Or:

```bash
.venv/bin/python -m playground db-init
```

**Fresh database** (wipe local dev data and re-seed):

```bash
rm -f /tmp/eden_playground.db /tmp/eden_playground.db-wal /tmp/eden_playground.db-shm
python -m playground db-init
```

If a legacy `playground.db` exists in the repo root, the first startup copies it into `/tmp` once; otherwise migrations create an empty schema and seed fills it.

**Test user with orbs on the map** (dev only):

```bash
python -m playground create-test-user --orbs clarity,wisdom
```

Prints a map URL with `?return_code=…` that logs you in and shows granted orbs from `journey.orbs` player state.

### Run the dev server

With the venv activated (runs migrations + seed on startup if not already done):

```bash
uvicorn playground.main:app --reload --host 0.0.0.0 --port 8000
```

Or without activating the shell (project venv):

```bash
.venv/bin/uvicorn playground.main:app --reload --host 0.0.0.0 --port 8000
```

### URLs

- API docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin/ (no login by default; set `ADMIN_AUTH_ENABLED=true` and credentials to lock it down)
- **Player journey:** http://localhost:8000/ → intro lab → consent → demo → map
- **Map scene (orb slider):** http://localhost:8000/worlds/map_world/scenes/map/view
- Sample world: http://localhost:8000/worlds/deal_world/scenes/intro/view

### Tests

With the venv activated:

```bash
pytest
```

See [playground/README.md](playground/README.md) and [docs/architecture.html](docs/architecture.html) for backend detail.

## View the static docs site locally

Opening the HTML files via `file://` will usually break JSON loading (`fetch(...)`). Start the local server:

```powershell
cd .\docs
.\serve.ps1
```

Then open `http://localhost:5173/index.html`.
