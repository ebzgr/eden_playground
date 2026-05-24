# eden_playground

**eden_playground** is a small static website for **Marketing for Betterment's playground**: a research + awareness platform that makes manipulative marketing techniques more visible through immersive, art-driven “worlds”, and documents the conceptual, ethical, and methodology layers behind that work.

## What’s in this repo

- `docs/`: the site (static HTML/CSS/JS) and its wiki-style navigation.
- `playground/`: **v0 backend** (FastAPI) — event tracker, world builder, A/B testing, player state, admin dashboard, **Demo SDK** (`demo.yaml` scroll-scrubbed scenes).
- `Documents/`: reference PDFs used by the project.

## Run the platform API

```bash
# Use a venv on a local filesystem if pip/venv fails on mounted drives
pip install -e ".[dev]"
uvicorn playground.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs  
- Admin: http://localhost:8000/admin/ (default user/password: `admin` / `admin`)  
- Sample world: http://localhost:8000/worlds/deal_world/scenes/intro/view  

See [playground/README.md](playground/README.md) and [docs/architecture.html](docs/architecture.html).

## View locally

Opening the HTML files via `file://` will usually break JSON loading (`fetch(...)`). Start the local server:

```powershell
cd .\docs
.\serve.ps1
```

Then open `http://localhost:5173/index.html`.

