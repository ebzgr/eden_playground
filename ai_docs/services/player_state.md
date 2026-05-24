# Service: player_state

## What this service does

Per-user key-value store for in-world progress. Each mutation emits a `state_changed` event in the same transaction so the event log captures the change.

## Key files

- [`playground/services/player_state/router.py`](../../playground/services/player_state/router.py) — `GET /state`, `GET /state/{key}`, `POST /state/{key}` (set), `PATCH /state/{key}` (op).
- [`playground/services/player_state/service.py`](../../playground/services/player_state/service.py) — `get_all_state`, `get_state`, `set_state`, `patch_state`. `set_state` and `patch_state` call `emit_state_changed`.
- [`playground/services/player_state/ops.py`](../../playground/services/player_state/ops.py) — `apply_op(current, op, value)`. Ops: `set`, `inc`, `merge`, `append`, `remove`.
- [`playground/schemas/player_state.py`](../../playground/schemas/player_state.py).
- [`playground/models/player_state.py`](../../playground/models/player_state.py).

## Cookbook

### Read all state for the current user

```
GET /state
→ {"items": {"<key>": <value>, ...}}
```

### Read a single key

```
GET /state/<key>
→ {"key": "<key>", "value": <value-or-null>}
```

### Set a key

```
POST /state/<key>?session_id=...
Body: {"value": <any-json>}
Headers (optional): X-World-Id, X-Scene-Id   # included in the state_changed event
```

The body can also be any JSON literal; the router falls back to using the whole body as the value if `value` is missing (see [`router.py`](../../playground/services/player_state/router.py)).

### Apply an operation

```
PATCH /state/<key>?session_id=...
Body: {"op": "inc" | "append" | "remove" | "set" | "merge", "value": <typed-per-op>}
```

| op | current type | value type | result |
|---|---|---|---|
| `set` | any | any | replaces current with value |
| `inc` | number or null | number (default 1) | numeric add |
| `append` | list or null | item | new list with item appended |
| `remove` | list | item | new list without item (first occurrence) |
| `merge` | dict or null | dict | shallow merge |

### Emit a state_changed event from another server module

`emit_state_changed(db, user, session_id, key, op, old_value, new_value, world_id, scene_id)` from [`event_tracker/service.py`](../../playground/services/event_tracker/service.py). Consent is checked inside; safe to call.

## Reference

### `state_changed` event payload

```json
{
  "key": "<key>",
  "op": "set" | "inc" | "append" | "remove" | "merge",
  "old_value": <prior>,
  "new_value": <new>
}
```

The event row also carries `world_id` / `scene_id` when the caller passed `X-World-Id` / `X-Scene-Id`.

### Model

`PlayerState`: `(user_id, key)` with a JSON `value`. Composite index on `(user_id, key)`.

## Gotchas

- The op set is closed. `apply_op` raises `ValueError` on unknown ops — surface that as a 400 if you wrap it.
- `append` / `remove` require list semantics. `merge` requires dict semantics. Type mismatches raise.
- `session_id` is required on every write because the resulting `state_changed` event needs it. The router enforces this via `Query(...)`.
- Writes flush + emit + return; the router commits. Don't introduce intermediate commits inside `service.py`.
