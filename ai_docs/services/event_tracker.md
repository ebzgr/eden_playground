# Service: event_tracker

## What this service does

Receives client-side events, gates them on consent and preview mode, and writes them to the append-only `events` table. Also emits server-side `state_changed` events from the player_state service.

## Key files

Server:

- [`playground/services/event_tracker/router.py`](../../playground/services/event_tracker/router.py) — `POST /events`; drops events when `X-Playground-Preview: 1` or `session_id` starts with `preview-`.
- [`playground/services/event_tracker/service.py`](../../playground/services/event_tracker/service.py) — `ingest_events(...)`, `emit_state_changed(...)`.
- [`playground/services/event_tracker/privacy.py`](../../playground/services/event_tracker/privacy.py) — `consent_allows_tracking(user)`.
- [`playground/schemas/event.py`](../../playground/schemas/event.py) — `EventItem`, `EventsIngestRequest`, `EventsIngestResponse`.
- [`playground/models/event.py`](../../playground/models/event.py) — `Event` ORM model.

Client (the SDK trio, loaded in this order by `render_scene_page`):

1. [`playground/static/sdk/playground.js`](../../playground/static/sdk/playground.js) — the **public surface**. Scene authors call `Playground.track`, `Playground.goToScene`, etc.
2. [`playground/static/sdk/tracker.js`](../../playground/static/sdk/tracker.js) — queue, batching, `POST /events`. Never called directly from scene JS.
3. [`playground/static/sdk/events.js`](../../playground/static/sdk/events.js) — auto lifecycle events (`scene_view`, `scene_exit`) and declarative `data-pg-event` bindings.

## Cookbook

### Fire a custom event from scene JS

Use the imperative API. Payload is an arbitrary JSON-serializable dict:

```js
Playground.track("lab_choice_selected", { option: "A", index: 0 });
```

`Playground.track` is a no-op in preview mode. The Tracker auto-attaches `experiment_id`, `arm_id`, `assignment_scope`, `scene_version_id`, `experiment_arms`, `world_id`, `scene_id`, `session_id`, and `ts_client`.

### Fire an event declaratively (preferred for UI interactions)

Add `data-pg-event` (and optional `data-pg-payload`) to the element:

```html
<button data-pg-event="lab_continue_clicked">Continue</button>

<input type="checkbox"
       data-pg-event="consent_toggled"
       data-pg-payload='{"context": "consent_scene"}'>
```

`events.js` scans the DOM at `init()`, binds `click` for buttons/links and `change` for inputs/selects/textareas, and merges form values (`checked`, `value`) into the payload. See `bindDeclarative()` and `formPayload()` in [`events.js`](../../playground/static/sdk/events.js).

### Naming convention

`{scope}_{verb}_{noun?}` in snake_case. Examples: `scene_view`, `scene_exit`, `consent_toggled`, `lab_continue_clicked`, `state_changed`. Keep scopes stable and verbs in past tense for user actions.

### Auto lifecycle events

`events.js` fires automatically — do not duplicate from scene code:

- `scene_view` on init. Payload may include `entered_from: {world, scene}` if a previous scene wrote to `sessionStorage["pg:prev_scene"]`.
- `scene_exit` on `pagehide` / `visibilitychange="hidden"`. Payload: `{duration_ms, reason}` where `reason` is `nav` (called via `Playground.goToScene`), `pagehide`, or `hidden`. Sent via `Tracker.sendImmediate` using `navigator.sendBeacon` or `fetch({keepalive: true})`.

### Server-emit a state_changed event

`emit_state_changed(...)` in [`service.py`](../../playground/services/event_tracker/service.py) is called from [`player_state/service.py`](../../playground/services/player_state/service.py) inside the same transaction as the state mutation. Caller must ensure consent.

## Reference

### `EventItem` shape

| Field | Type | Notes |
|---|---|---|
| `event_type` | str | required, snake_case |
| `payload` | dict / list / None | merged with auto-attached experiment fields client-side |
| `world_id`, `scene_id`, `scene_version_id` | str / None | auto-attached by tracker |
| `experiment_arms` | dict | `{<experiment_id>: {arm_id, assignment_scope}}` |
| `ts_client` | ISO datetime | tracker sets `new Date().toISOString()` |

Server adds `ts_server` and `user_id` on insert.

### Endpoint

`POST /events`

Body: `{session_id, events: [EventItem, ...]}`
Auth: cookie or `X-Return-Code` header (resolved by `CurrentUser`).
Drops the entire batch (returns `accepted: 0`) if `X-Playground-Preview: 1` **or** `session_id` starts with `preview-`.

### Preview-mode contract

Three signals must always agree:

1. `window.__PLAYGROUND__.previewMode === true`
2. Outgoing requests carry `X-Playground-Preview: 1`
3. Session id is `preview-<worldId>`

`tracker.js` and `playground.js` enforce (1) → (2) and (1) → (3). The server enforces (2) and (3) → drop.

## Gotchas

- The queue flushes 2 seconds after enqueue (`scheduleFlush`). For unload events use `Tracker.sendImmediate`, which already takes care of `sendBeacon`/`keepalive`. `events.js` does this for `scene_exit`.
- `consentGranted` defaults to `false` in `tracker.js`. It flips to `true` only when `/identity` returns `consent_state: "granted"` or when `setConsentGranted(true)` is called. In preview, it is forced to `false`.
- `payload` must be JSON-serializable. Don't pass DOM elements; copy out `el.value` / `el.checked` instead.
- Server `emit_state_changed` does **not** check preview at the call site — it relies on the caller (the state mutation path) being inside a real user request. Don't reuse it for arbitrary server-side logging without a consent check.
- Renaming an `event_type` is a soft data-model break; existing rows still carry the old name. Document the change in [`/docs/Architecture.md`](../../docs/Architecture.md).
