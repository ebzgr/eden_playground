# Testing conventions

Small, fast pytest suite. Async-first.

## Where tests live

All tests are flat under [`tests/`](../../tests/). One file per feature area, mirroring service boundaries:

| File | Covers |
|---|---|
| [`tests/test_identity_and_events.py`](../../tests/test_identity_and_events.py) | identity router, return codes, consent, event ingestion happy path |
| [`tests/test_event_handler_payload.py`](../../tests/test_event_handler_payload.py) | scene_exit payload, preview-mode drop, X-Playground-Preview header drop |
| [`tests/test_world_builder.py`](../../tests/test_world_builder.py) | YAML loading, navigation defaults |
| [`tests/test_versioning.py`](../../tests/test_versioning.py) | version manifests, patcher ops |
| [`tests/test_ab_testing.py`](../../tests/test_ab_testing.py) | sticky vs session assignment, weighted picking |
| [`tests/test_experiment_lifecycle.py`](../../tests/test_experiment_lifecycle.py) | finish_if_expired, set_state, extend |
| [`tests/test_experiment_admin.py`](../../tests/test_experiment_admin.py) | slugify, resolve id, parse arms from form |
| [`tests/test_player_state.py`](../../tests/test_player_state.py) | KV ops, state_changed emission |
| [`tests/test_admin.py`](../../tests/test_admin.py), [`tests/test_admin_events.py`](../../tests/test_admin_events.py), [`tests/test_admin_lists.py`](../../tests/test_admin_lists.py) | admin Jinja routes, filters |
| [`tests/test_intro_flow.py`](../../tests/test_intro_flow.py), [`tests/test_e2e.py`](../../tests/test_e2e.py) | cross-service flows |

When adding a feature, **append to the matching file** rather than creating a parallel one. Create a new file only when the feature is genuinely orthogonal.

## Fixtures

All fixtures live in [`tests/conftest.py`](../../tests/conftest.py). Three you will use almost every time:

- `engine` — fresh schema; drops + recreates all tables via `Base.metadata`.
- `db_session` — async session, with worlds and a demo experiment seeded.
- `client` — `httpx.AsyncClient` against the FastAPI app, with `get_db` overridden onto the test session.

## Conventions

- Tests are `async def` and marked implicitly via `pytest-asyncio` config.
- One assertion concept per test. Multiple `assert` lines are fine when they verify the same behavior.
- Hit the HTTP boundary when testing routers; call service functions directly when testing logic.
- For experiments, build rows via `_live_exp(...)` style helpers (see [`tests/test_experiment_lifecycle.py`](../../tests/test_experiment_lifecycle.py)) so `starts_at` / `ends_at` / `name` / `explanation` are always populated.
- For events, post via the `client` fixture so the consent gate and preview-mode drop are exercised end-to-end.
- For preview-mode regressions, assert **both** entry paths: session id prefix `preview-` and `X-Playground-Preview: 1` header.

## Running

Use the project venv at `.venv/` (see root `README.md`). Standard run:

```bash
source .venv/bin/activate
pytest -q
```

Without activating:

```bash
.venv/bin/pytest -q
```

Single file:

```bash
.venv/bin/pytest -q tests/test_experiment_lifecycle.py
```

If the repo lives on a mount where `.venv` cannot be created, use `/tmp/eden_pg_venv` instead (same `pip install -e ".[dev]"` step).

If the test DB at `./test_playground.db` gets wedged, delete it and re-run; the `engine` fixture recreates it.

## When NOT to add a test

- Trivial property rename in a Pydantic schema with no behavior change.
- Pure formatting / typing fixes.

Otherwise: every fix that wasn't caught by an existing test deserves one.
