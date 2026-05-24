# Service: ab_testing

## What this service does

Assigns users (or sessions) to scene-version arms of live experiments. Manages experiment lifecycle: draft → live → paused → done, with an audit log and automatic finish at `ends_at`. Scope is **scene_version only**; navigation A/B testing has been removed.

## Key files

- [`playground/services/ab_testing/service.py`](../../playground/services/ab_testing/service.py) — `resolve_scene_version(...)`, internal `_find_active_scene_experiment` and `_get_or_assign_arm`.
- [`playground/services/ab_testing/assigner.py`](../../playground/services/ab_testing/assigner.py) — `pick_arm(subject_id, experiment_id, arms)`: weighted seeded selection via `blake2b(subject || experiment, salt=server_salt)`.
- [`playground/services/ab_testing/lifecycle.py`](../../playground/services/ab_testing/lifecycle.py) — `set_experiment_state`, `extend_experiment`, `finish_if_expired`, `sync_expired_experiments`, `experiment_is_assignable`, `utcnow`, `as_utc`, `record_history`, `list_experiment_history`.
- [`playground/services/ab_testing/defaults.py`](../../playground/services/ab_testing/defaults.py) — `experiment_schedule(...)` for seed and tests.
- [`playground/services/ab_testing/router.py`](../../playground/services/ab_testing/router.py) — `GET /assignments/scene/{world}/{scene}`.
- [`playground/services/admin/experiment_admin.py`](../../playground/services/admin/experiment_admin.py) — admin-side CRUD helpers: `create_experiment`, `parse_arms_from_form`, `resolve_experiment_id`, `slugify_experiment_id`, `default_schedule`, `parse_admin_datetime`, `get_experiment_detail_context`.
- [`playground/models/experiment.py`](../../playground/models/experiment.py) and [`playground/models/experiment_status_history.py`](../../playground/models/experiment_status_history.py).
- [`playground/schemas/experiment.py`](../../playground/schemas/experiment.py).

## Cookbook

### Create an experiment programmatically (seed or migration)

```python
from playground.services.admin.experiment_admin import create_experiment
from playground.services.ab_testing.defaults import experiment_schedule

starts_at, ends_at = experiment_schedule(start_days_ago=0, duration_days=14)
exp = await create_experiment(
    db,
    id="exp_consent_tone",
    name="Consent copy tone",
    assignment_scope="user",
    world="intro_world",
    scene="consent",
    arms=[
        {"id": "control",  "version": "base",    "weight": 1},
        {"id": "trust",    "version": "trust",   "weight": 1},
        {"id": "playful",  "version": "playful", "weight": 1},
    ],
    explanation="Compare neutral, trust-building, and playful consent copy ...",
    starts_at=starts_at,
    ends_at=ends_at,
    state="draft",   # always start draft; Ethics gates the flip to live
)
```

`create_experiment` writes an `experiment_status_history` row with `action="created"`.

### Create via admin UI

`GET /admin/experiments/new` → fill form → `POST /admin/experiments`. Form handler:

- `name` is required; `id` is optional and slugified from `name` if blank (via `resolve_experiment_id`).
- Arms are repeated form fields: `arm_id`, `arm_version`, `arm_weight` arrays parsed by `parse_arms_from_form`. Minimum two arms.
- `starts_at` / `ends_at` are `datetime-local` strings; parsed by `parse_admin_datetime` as UTC.
- `explanation` is free text and shows up in the detail page.

### Change state, extend, finish

Lifecycle helpers in [`lifecycle.py`](../../playground/services/ab_testing/lifecycle.py):

- `set_experiment_state(db, exp, "live"|"paused"|"draft"|"done", note=...)` — logs `experiment_status_history`.
- `extend_experiment(db, exp, extra_days, note=...)` — bumps `ends_at`, logs.
- `finish_if_expired(db, exp)` — automatic move to `done` if past `ends_at`.
- `sync_expired_experiments(db)` — runs at the top of the admin experiments list and detail pages.

Admin endpoints:

- `POST /admin/experiments/{id}/state` with `new_state`, `note`.
- `POST /admin/experiments/{id}/extend` with `extra_days`, `note`.

### Read what arm a user got

`GET /assignments/scene/{world}/{scene}?user_id=...&session_id=...&default_version_id=...` returns `SceneAssignmentResponse`. Usually you don't call this directly — `resolve_scene` does it during the scene view.

## Reference

### Experiment model

```
id              (PK, str)
name            (str) human-readable
target_scope    "scene_version" (always for new experiments)
assignment_scope "user" | "session"
target          {"world": ..., "scene": ...}
arms            [{id, version, weight}, ...]
guardrails      JSON (currently unused)
state           "draft" | "live" | "paused" | "done"
starts_at       UTC-aware datetime
ends_at         UTC-aware datetime
explanation     text
created_at      server default
```

### Assignment semantics

`resolve_scene_version` runs at scene resolve time:

1. Find a scene-version experiment for `(world, scene)` whose state is `live` or `paused`.
2. Call `finish_if_expired` and skip if it just moved to `done`.
3. Call `experiment_is_assignable`: only `live` and `starts_at ≤ now < ends_at` will assign new subjects.
4. If `assignment_scope == "user"`: look up `assignments` for `(experiment_id, subject_type="user", subject_id=str(user_id))`; reuse arm if present, otherwise `pick_arm` and persist.
5. If `assignment_scope == "session"`: `pick_arm` on the session_id, no persistence.

`pick_arm` is deterministic on `(subject_id, experiment_id, server_salt)`. Same inputs always pick the same arm.

### Lifecycle states

| State | Assigns new subjects? | Stickiness honored? | Notes |
|---|---|---|---|
| `draft` | no | n/a | not surfaced to users at all |
| `live` | yes (within window) | yes | normal running state |
| `paused` | no | yes | sticky users still see their arm |
| `done` | no | n/a | terminal; reached by manual finish or auto on `ends_at` |

### Audit log

`experiment_status_history`: `id, experiment_id, action, previous_state, new_state, previous_ends_at, new_ends_at, note, created_at`. Actions: `created`, `live`, `paused`, `finished`, `extended`, `draft`, `status_change`.

## Gotchas

- SQLite returns naive datetimes for `starts_at` / `ends_at`. **Always** route through `as_utc()` before comparing — see [`lifecycle.py`](../../playground/services/ab_testing/lifecycle.py).
- Changing `server_salt` re-buckets every subject. Treat it as immutable in any environment with real data.
- Adjusting arm weights mid-flight does not redistribute existing sticky users. It only changes the bucket math for new ones.
- An experiment in `paused` is **still assignable to existing sticky users** (they see their arm), but no new subjects are added.
- `target_scope` exists on the model but is always `"scene_version"` for new experiments. Filtering by it is fine; do not extend it without an Architect review.
- Always start experiments in `draft`; the Ethics Reviewer role gates the transition to `live`.
