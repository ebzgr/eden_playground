# Coding conventions

Concrete rules. Skim before editing; obey while editing.

## Stack

- Python 3.12, FastAPI, async SQLAlchemy 2 (declarative `Mapped[...]`).
- SQLite by default at `/tmp/eden_playground.db` (see [`playground/config.py`](../../playground/config.py)). Tests use `./test_playground.db`.
- Alembic migrations live in [`alembic/versions/`](../../alembic/versions/). `init_db()` in [`playground/db.py`](../../playground/db.py) runs them on startup.
- Frontend: Jinja2 + Bootstrap 5 for admin; vanilla JS + plain HTML/CSS for player scenes; Chart.js where needed.

## Module layout (do not deviate)

```
playground/
  config.py           settings via env vars
  db.py               engine, session factory, Alembic bootstrap
  deps.py             CurrentUser / OptionalUser / DbSession / get_return_code
  main.py             FastAPI app + router wiring
  seed.py             demo data
  models/             SQLAlchemy ORM models (one file per table)
  schemas/            Pydantic request/response schemas
  identity/           top-level identity package (router + service)
  services/<svc>/
    router.py         FastAPI routes
    service.py        business logic, returns Pydantic or ORM objects
    <extras>.py       feature-specific modules (lifecycle, patcher, etc.)
  static/sdk/         player-facing JS (playground.js, tracker.js, events.js)
  worlds_content/<world_id>/
    world.yaml
    scenes/<scene_id>/
      base.{html,css,js}
      versions/<version>.yaml
```

When adding a service, mirror this layout. The Architect role gates new top-level services.

## Imports

- Absolute imports rooted at `playground.` Never `from . import x` across packages.
- No wildcard imports.
- No unused imports — they trigger lints.
- Sort: stdlib, third-party, `playground.*`. One blank line between groups.

## Async + DB

- All routes are `async def`. Get the session via `db: DbSession` from [`playground/deps.py`](../../playground/deps.py).
- `await db.flush()` after writes inside a service; commit at the router boundary (`await db.commit()`).
- For datetime comparisons across SQLite and ORM use `as_utc()` from [`playground/services/ab_testing/lifecycle.py`](../../playground/services/ab_testing/lifecycle.py). SQLite returns naive `datetime`s; comparing against `datetime.now(timezone.utc)` will raise without normalization.
- Always use `datetime.now(timezone.utc)` and `DateTime(timezone=True)` columns. Never `datetime.utcnow()`.

## Schemas vs models

- ORM `Mapped[...]` types live in `playground/models/`. Each file is one table.
- Pydantic schemas live in `playground/schemas/`. `model_config = {"from_attributes": True}` for outbound schemas reading ORM.
- Routes never accept or return raw ORM objects across the API boundary — convert to schemas.

## Function / variable naming

- Functions: `snake_case`, verbs (`resolve_scene`, `pick_arm`, `set_experiment_state`).
- Pydantic / ORM classes: `PascalCase`.
- Constants and env-driven settings: `UPPER_SNAKE`.
- Booleans read like predicates: `is_preview`, `has_variants`, `experiment_is_assignable`.

## JS SDK (player-facing)

Three files in `playground/static/sdk/`, loaded in this order by [`playground/services/world_builder/render.py`](../../playground/services/world_builder/render.py):

1. `playground.js` — public surface: `Playground.track`, `Playground.goToScene`, `Playground.initTracker`, etc.
2. `tracker.js` — queue + `/events` POST. Never call directly from scene JS.
3. `events.js` — auto `scene_view` / `scene_exit`, declarative `data-pg-event` bindings.

Scene authors call **only** `Playground.*`. Prefer `data-pg-event="..."` over hand-written listeners; fall back to `Playground.track(eventType, payload)` only when DOM-only binding is insufficient.

`window.__PLAYGROUND__` is set by the page shell and contains `worldId`, `sceneId`, `sessionId`, `versionId`, `experiment`, `experimentArms`, `nav`, `previewMode`. Treat it as read-only configuration.

## Responsive UI baseline

Every player scene and admin page must be usable on a phone in portrait without horizontal scrolling.

The shells already set the right baseline:

- Player scene shell — [`playground/services/world_builder/render.py`](../../playground/services/world_builder/render.py) emits `<meta name="viewport" content="width=device-width, initial-scale=1"/>`.
- Admin shell — [`playground/services/admin/templates/base.html`](../../playground/services/admin/templates/base.html) emits the same viewport meta and uses Bootstrap 5's responsive grid.

Do not undo either.

**For scene CSS, prefer fluid-first patterns over breakpoints.** The existing scenes (see [`playground/worlds_content/intro_world/scenes/consent/base.css`](../../playground/worlds_content/intro_world/scenes/consent/base.css)) achieve responsive layout with just three habits:

1. **Use `rem` for sizes**, not `px` for anything that should scale (font, padding, max-width, gaps). Reserve `px` for hairlines (`1px` borders) and exact pixel artifacts.
2. **Cap content with `max-width` and let padding absorb the rest.** Cards are typically `max-width: 24rem – 40rem` inside a `padding: 1.5rem` flex container. On a narrow viewport the card naturally shrinks to `100vw - 2 * padding`.
3. **Fill the viewport, no document scroll by default.** [`render.py`](../../playground/services/world_builder/render.py) injects shell CSS: `html` and `body.pg-scene` are `height: 100%; overflow: hidden`, and `body.pg-scene > main` is `height: 100%` with `overflow: hidden`. Style the scene's `<main>` with flex centering and `clamp()` padding so content fits phones without growing the page. Do **not** add `min-height: 100vh` on both `body` and `<main>` — that stacks past the viewport and forces a scrollbar.

4. **Opt-in scroll only when needed.** Long informational scenes (e.g. `intro_world/about`) add `document.body.classList.add("pg-scene--scroll")` in scene JS so the shell allows vertical scrolling. Do not enable scroll for standard journey scenes unless the design explicitly requires it.

Add a `@media (max-width: <Xrem>)` block only when fluid layout genuinely cannot reflow — e.g. you need to stack a side-by-side layout vertically, or hide a non-essential decoration. Default to no breakpoint.

**Other responsive requirements:**

- **Tap targets** at least `2.5rem × 2.5rem` for any interactive element on a scene (buttons, checkboxes, links acting as buttons).
- **No fixed-width containers** unless the intent is explicitly desktop-only and the route is admin-only.
- **No horizontal scroll** on the page body at any viewport ≥ `320px`.
- **No vertical scroll** on player scenes unless `body.pg-scene--scroll` is set (see item 4 above). Tester must verify this on every touched scene.
- **Respect `prefers-reduced-motion`** for any animation longer than ~200ms.
- **Touch + mouse** — never rely on `:hover` alone to expose information; `:hover` may augment a state that is also reachable by `:focus`, `aria-expanded`, or a tap.

## Preview mode discipline

Three signals carry preview status; **all three must remain in sync**:

1. `window.__PLAYGROUND__.previewMode === true` — set by `render_scene_page(resolved, preview_mode=True)`.
2. Outgoing requests carry `X-Playground-Preview: 1` (handled by `tracker.js` and `playground.js`).
3. The session id is `preview-<world>` (set by `Playground.ensureWorldSession` in preview).

The server drops events when **either** the header is `"1"` **or** the session id starts with `preview-` (see [`playground/services/event_tracker/router.py`](../../playground/services/event_tracker/router.py)).

If you add a new client path that posts to the server, you must respect all three. If you add a new server endpoint that ingests user data, you must honor preview at the entry point.

## Comments

- Comments explain non-obvious intent or constraints. Never restate the next line.
- Module docstrings describe the file's role in one sentence.
- Avoid emoji in code, comments, and docs unless the user explicitly asks.
