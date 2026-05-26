# Service: world_builder

## What this service does

Loads worlds, scenes, and scene versions from disk; resolves which scene version a given user/session should see; renders the full HTML page shell that boots the JS SDK.

## Key files

- [`playground/services/world_builder/service.py`](../../playground/services/world_builder/service.py) — `load_world_yaml`, `load_scene_files`, `resolve_scene` (authed), `resolve_scene_guest` (public/preview), `list_scenes_for_world`, `list_scene_versions`, `transition`.
- [`playground/services/world_builder/patcher.py`](../../playground/services/world_builder/patcher.py) — `resolve_version`, `discover_versions`, `PATCH_OPS` (the only DOM op vocabulary).
- [`playground/services/world_builder/demo_config.py`](../../playground/services/world_builder/demo_config.py) — load/validate `demo.yaml`, mobile merge.
- [`playground/services/world_builder/render.py`](../../playground/services/world_builder/render.py) — `render_scene_page(resolved, preview_mode=False)`: builds the `<!DOCTYPE html>`, injects `window.__PLAYGROUND__`, loads the SDK trio, and renders the preview banner when applicable. Injects GSAP + Demo SDK when `demo.yaml` is present.
- [`playground/static/sdk/conversation.js`](../../playground/static/sdk/conversation.js) — optional SDK helper. Add `class="conversation"` to any container to animate its text word-by-word. Scene HTML loads it explicitly: `<script src="/static/sdk/conversation.js"></script>`. Buttons inside are hidden until animation ends. Click skips to end. Attributes: `data-word-delay` (ms, default 75), `data-comma-pause` (default 220), `data-period-pause` (default 400).
- [`playground/services/world_builder/router.py`](../../playground/services/world_builder/router.py) — `GET /worlds`, `GET /worlds/{w}/scenes/{s}` (JSON), `GET /worlds/{w}/scenes/{s}/view` (HTML), `GET /worlds/{w}/scenes/{s}/assets/{path}`, `POST /worlds/{w}/scenes/{s}/transition`.

Content lives under [`playground/worlds_content/<world>/`](../../playground/worlds_content/).

## Cookbook

### Add a new world

1. Create `playground/worlds_content/<world_id>/world.yaml` with at minimum:
   ```yaml
   id: <world_id>
   name: Human-readable name
   default_scene: <scene_id>
   public_scenes: [<scenes visitable without identity>]
   scene_versions: { <scene_id>: base, ... }
   navigation:
     <scene_id>:
       <event>: <next_scene_id>
   ```
2. Create at least the default scene under `scenes/<scene_id>/base.{html,css,js}`.
3. Restart or hit `/worlds` to pick up the new world via `list_worlds()` (DB row is created by [`playground/seed.py`](../../playground/seed.py)'s `_sync_worlds_from_disk` on next start).

### Add a new scene to an existing world

1. Create `scenes/<scene_id>/base.{html,css,js}`.
2. If publicly visitable (no identity required), add `<scene_id>` to `world.yaml`'s `public_scenes`.
3. Add navigation edges in `world.yaml`'s `navigation:` block, e.g. `continue: next_scene`.
4. Set the scene's default version in `scene_versions:`, usually `base`.

### Add a scene version (variant)

One YAML manifest per version under `scenes/<scene_id>/versions/<version_id>.yaml`. Manifest fields (all optional):

| Field | Use |
|---|---|
| `id` | defaults to file stem |
| `description` | two-line intent statement |
| `html` / `css` / `js` | full replacement files for substantial reskins |
| `patches` | list of DOM ops applied to the resolved HTML |
| `css_append` | appended after the resolved CSS |
| `js_append` | appended after the resolved JS |
| `nav_overrides` | `{event: next_scene}` merged into the scene's default nav |

Prefer `patches` + `css_append` for surgical tweaks; use the full file replacements only when the reskin is substantial. See [`playground/worlds_content/intro_world/scenes/consent/versions/trust.yaml`](../../playground/worlds_content/intro_world/scenes/consent/versions/trust.yaml) for the patcher pattern.

### Add a demo scene (`demo.yaml`)

A scene is a **demo scene** when `scenes/<scene_id>/demo.yaml` exists. See [`ai_docs/services/demo_framework.md`](../demo_framework.md) for the full schema. Summary:

1. Create `demo.yaml` alongside `base.{html,css,js}`.
2. Minimal `base.html`: `<main id="demo-root">` plus any static controls (e.g. `#btn-continue`).
3. Minimal `base.js`: `Demo.run(window.__DEMO__)`.
4. Optional assets under `assets/` — served at `/worlds/<w>/scenes/<s>/assets/<file>`.
5. **Shared character art** under [`playground/worlds_content/characters/`](../../playground/worlds_content/characters/) — served at `/worlds/characters/<character_id>/<file>` (e.g. `/worlds/characters/gaia/portrait.png`). See that folder’s `README.md`.
5. `render_scene_page` auto-injects `demo.css`, GSAP, ScrollTrigger, `demo.js`, and `window.__DEMO__`. Non-demo scenes are unchanged.

Author demos with the **demo_builder** role; do not modify the SDK from scene work.

### Patcher op vocabulary

Defined in `PATCH_OPS` in [`patcher.py`](../../playground/services/world_builder/patcher.py):

`setText`, `setHtml`, `setAttr`, `removeAttr`, `addClass`, `removeClass`, `appendInside`, `prependInside`, `insertBefore`, `insertAfter`, `remove`.

Each patch is `{op: <op>, selector: <CSS selector>, ...op-specific fields}`. Selectors must be valid CSS (lxml `cssselect`).

### Preview a version without going through assignment

- Player view, force a version: `/worlds/<world>/scenes/<scene>/view?force_version=<id>`
- Admin preview (no telemetry): `/admin/worlds/<world>/scenes/<scene>/preview?version=<id>` — uses `resolve_scene_guest` + `render_scene_page(..., preview_mode=True)`.

## Reference

### Resolution pipeline

```
GET /worlds/{w}/scenes/{s}/view
  → resolve_scene (authed) | resolve_scene_guest (public)
    → load_world_yaml + load_scene_files (base.{html,css,js}) + load_demo_yaml (optional)
    → resolve_scene_version (ab_testing) → chosen version_id
    → resolve_version (patcher): apply manifest html/css/js + patches + css_append + js_append
    → render_scene_page: assemble HTML shell, inject window.__PLAYGROUND__ (+ demo SDK if demo.yaml)
  → HTMLResponse
```

### Schemas

[`playground/schemas/world.py`](../../playground/schemas/world.py): `WorldSummary`, `SceneResolved`, `TransitionRequest`, `TransitionResponse`.

### Models

[`playground/models/world.py`](../../playground/models/world.py) and [`playground/models/scene.py`](../../playground/models/scene.py). Seeded by [`playground/seed.py`](../../playground/seed.py) from the on-disk `world.yaml`.

### `map_world` (legacy index port)

Eight scenes from [`legacy/index.html`](../../legacy/index.html), with click navigation instead of scroll:

| Scene | Role |
|---|---|
| `welcome` | Legacy `#welcome` — typing subtitle, **Explore the map** → `map` |
| `map` | Legacy `#worlds` — six door cards → `door_*` |
| `door_urgency` … `door_persuasion` | Legacy sections `#urgency`, `#gamification`, `#social-proof`, `#pricing`, `#framing`, `#advertising` — each has **Back to map** |

Intro flow: lab → consent → **demo** → map. Consent sends players to `intro_world` / `demo`; demo continues via `PG.goToScene("map_world", "welcome", …)`.

## Gotchas

- `resolve_scene_guest` does not assign A/B versions and does not write sessions — it is only for public or preview paths.
- `force_version` bypasses experiments. Useful for previewing; never user-facing in the normal flow.
- Unknown version ids silently fall back to `base` (see `resolve_version`). Do not rely on a 404 to detect misnamed manifests; check `discover_versions(scene_dir)` instead.
- The HTML page shell loads `playground.js`, `tracker.js`, `events.js` in that order. Scene JS runs last. Do not change the order without updating dependents.
- Preview mode: fixed banner overlays the top; `<main>` gets `padding-top: 2.25rem` via shell CSS (`body[data-preview="true"] > main`), not `body` padding — avoids document scroll.
- Default player scenes: shell sets `html`/`body`/`main` to `height: 100%; overflow: hidden`. Long pages opt in with `body.pg-scene--scroll` in scene JS. Do not use stacked `min-height: 100vh` on both `body` and `<main>`.
- The shell sets `<meta name="viewport" content="width=device-width, initial-scale=1"/>`. Do not remove it — every scene must be mobile-friendly. Follow the **Responsive UI baseline** in [`ai_docs/conventions/coding.md`](../conventions/coding.md): `rem` sizing, `max-width` + flex centering, fluid-first, breakpoints only when reflow fails.
