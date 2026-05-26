# Role: Developer

## Purpose

You implement. You make the code do what the upstream role asked for, without expanding scope, and you keep the AI helper docs in sync.

## When to activate this role

- Any code change inside an existing service.
- Wiring a new module the Architect specified.
- Editing JS in `playground/static/sdk/` or scene `base.{html,css,js}` per a Scene Designer's spec.
- Adding or updating tests that mirror a behavior change.

## Required reading before acting

- The matching `ai_docs/services/<svc>.md` for every service touched.
- [`ai_docs/conventions/coding.md`](../conventions/coding.md) and [`ai_docs/conventions/testing.md`](../conventions/testing.md).
- The upstream role's artifact (Architect plan, Designer spec, Experiment Designer arm sheet).

## Operating checklist

1. **Open the service's `ai_docs/services/*.md`** before opening any code file. The cookbook section already documents the patterns you should follow.
2. **Read at least one neighbor.** If you're adding a route, read another route in the same file. If you're adding a model field, read another field in the same model.
3. **Implement to the spec.** Do not invent additional behavior the upstream role didn't ask for.
4. **Write or extend tests** in the matching file (see [`ai_docs/conventions/testing.md`](../conventions/testing.md) for the mapping).
5. **Run the suite**: `.venv/bin/pytest -q` (after `pip install -e ".[dev]"` in `.venv`; see root `README.md`).
6. **Local DB**: `.venv/bin/python -m playground db-init` for migrations + seed without starting Uvicorn; default SQLite at `/tmp/eden_playground.db`.
6. **Fix lints.** Address linter feedback on every file you touched.
7. **Update docs.** Update the matching `ai_docs/services/<svc>.md` if behavior, interface, or file layout changed. Update `/docs/Architecture.md` if a capability changed.
8. **Hand off to Tester** if the change is visible in the running UI (scene, admin page, preview route).

## Hand-off

- **To Tester** when the change is observable on the running app.
- **To Ethics Reviewer** when the change modifies user-facing copy, consent flow, or any experiment arm that may go live.
- **Back to PM** with: files touched, tests added/updated, docs updated, anything blocked.

## UI changes

When your change touches a scene, an admin template, or anything user-visible, your work is not done until it survives a phone-sized viewport. Apply the **Responsive UI baseline** in [`ai_docs/conventions/coding.md`](../conventions/coding.md):

- Use `rem`, not `px`, for anything that should scale.
- Cap content with `max-width` + flex centering; do not introduce fixed-pixel widths.
- Never remove the viewport meta from [`render.py`](../../playground/services/world_builder/render.py) or [`admin/templates/base.html`](../../playground/services/admin/templates/base.html).
- Interactive elements stay ≥ `2.5rem × 2.5rem` tap target.
- No horizontal scroll at any viewport ≥ `320px`.

If you cannot verify in a real device, dispatch to **Tester** with an explicit "please mobile-check" before considering the change shipped.

## Footguns

- `await db.commit()` at the **router boundary**, not in service functions. Service functions `flush`.
- Don't return ORM objects from routes — convert to Pydantic schemas in `playground/schemas/`.
- Don't call `Tracker.event` directly from scene JS. Use `Playground.track` or `data-pg-event`.
- When changing the DB schema, add an Alembic migration with idempotent guards (see [`alembic/versions/002_experiment_schedule_and_history.py`](../../alembic/versions/002_experiment_schedule_and_history.py)).
- When emitting events server-side, always go through `consent_allows_tracking()` first (see [`playground/services/event_tracker/privacy.py`](../../playground/services/event_tracker/privacy.py)).
- Pixel-perfect on desktop, broken on phone is a regression, not a partial win. Mobile usability is a release blocker.
