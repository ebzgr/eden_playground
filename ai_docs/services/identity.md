# Service: identity

## What this service does

Pseudonymous user identity via a **return code**: a 128-bit random token (base32, 26 chars) the user receives once and presents on later visits via cookie or `X-Return-Code` header. The DB stores only a salted blake2b hash of the code — never the raw code. Also handles consent state, session bootstrapping per world, and user erasure (right-to-be-forgotten).

## Key files

- [`playground/identity/router.py`](../../playground/identity/router.py) — `POST /identity`, `POST /consent`, `DELETE /me`.
- [`playground/identity/service.py`](../../playground/identity/service.py) — `mint_return_code`, `hash_return_code`, `get_or_create_user`, `ensure_session`, `record_consent`, `erase_user`.
- [`playground/deps.py`](../../playground/deps.py) — `CurrentUser`, `OptionalUser`, `get_return_code` (cookie or header).
- [`playground/models/user.py`](../../playground/models/user.py), [`playground/models/session.py`](../../playground/models/session.py), [`playground/models/consent.py`](../../playground/models/consent.py).

## Cookbook

### Mint a user (or recognize a returning one)

`POST /identity` with no body. If a cookie or `X-Return-Code` header is present, the existing user is returned; otherwise a new code and user are minted. Response:

```json
{
  "return_code": "OPAQUEBASE32...",
  "user_id": "<uuid>",
  "consent_state": "pending" | "granted" | "denied",
  "created": true
}
```

The server also sets the `return_code` cookie (`settings.return_code_cookie`, `max_age = 365 days`).

### Record consent

`POST /consent` with `{"state": "granted"|"denied"}`. Writes the new state on the `users` row and appends a row to `consents` for auditability. The `event_tracker` will only persist events while `users.consent_state == "granted"` (see [`event_tracker/privacy.py`](../../playground/services/event_tracker/privacy.py)).

### Ensure a per-world session

`ensure_session(db, user_id, world_id, session_id, stored_world_id)` reuses the existing session row if `session_id` is known and `stored_world_id == world_id`; otherwise mints a new UUID and writes a `sessions` row. Called from `resolve_scene` inside `world_builder/service.py`.

Client-side, this is wrapped by `Playground.ensureWorldSession(worldId)` in [`static/sdk/playground.js`](../../playground/static/sdk/playground.js), with localStorage keyed by `"playground_session"`.

### Erase a user

`DELETE /me` with cookie or `X-Return-Code`. Deletes all `events`, `player_state`, `assignments`, `consents`, `sessions`, and the `users` row in that order. Returns `{"deleted": true}`.

## Reference

### Return code lifecycle

```
client                       server
------                       ------
POST /identity (no code) --> mint code, hash, create user, set cookie
                         <-- {return_code, user_id, ...}
   localStorage["return_code"] = return_code

POST /identity (code) -----> hash, lookup, return user
                         <-- {return_code, user_id, ...}

POST /events (cookie or X-Return-Code) -> CurrentUser dep resolves user
```

### Auth pattern in FastAPI

```python
from playground.deps import CurrentUser, OptionalUser

@router.post("/something")
async def do_thing(user: CurrentUser, ...): ...

@router.get("/public-ish")
async def maybe(user: OptionalUser = None, ...): ...
```

`CurrentUser` 401s on missing/unknown code; `OptionalUser` returns `None`.

### Hashing

`hash_return_code` uses `blake2b(code, salt=server_salt[:16].ljust(16, b'\0'), digest_size=32)`. The DB stores the hex digest on `users.user_id_hash`. **Never** log or persist the raw code.

## Gotchas

- `server_salt` (in [`config.py`](../../playground/config.py)) participates in both the return-code hash and the experiment bucket hash. Changing it invalidates every existing return code and re-buckets every assignment. Treat as immutable post-deploy.
- The return code is the only credential. Losing it is irrecoverable by design — that's the privacy property. Do not add a recovery flow that re-binds a hash to a new pseudonym; that would defeat the point.
- `set_cookie` is `httponly=False` so JS can read it for SDK fallback. That is intentional given the SDK calls `/identity` directly with the cookie. Do not flip without rethinking the SDK.
- In preview mode, `Playground.postIdentity` and `Playground.postConsent` are no-ops. The SDK uses a synthetic `preview-<world>` session id; no users or consent rows are created.
- `erase_user` calls `await db.commit()` itself (because it executes raw deletes in sequence). Do not wrap it in another transaction or you'll get a nested-commit error.
