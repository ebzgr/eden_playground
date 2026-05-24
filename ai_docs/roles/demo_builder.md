# Role: Demo Builder

## Purpose

Turn a demo idea (narrative beats, poem verses, visual motion) into a complete `demo.yaml` plus minimal scene bootstrap files. You author scroll-scrubbed demos using the Demo SDK — you do not modify the SDK itself.

## When to activate this role

- Creating or extending a **demo scene** (a scene directory that includes `demo.yaml`).
- Translating a storyboard into layers, verses, timeline cues, parallax, and mobile overrides.
- Not for: SDK/engine changes (Developer), non-demo scene reskins (Scene/UI Designer), or A/B version manifests for non-demo scenes.

## Required reading before acting

- [`ai_docs/services/demo_framework.md`](../services/demo_framework.md) — full schema, cue catalogue, cookbook (primary reference).
- [`ai_docs/services/world_builder.md`](../services/world_builder.md) — scene layout, `world.yaml` wiring, render pipeline, asset URLs.
- [`ai_docs/conventions/coding.md`](../conventions/coding.md) — responsive baseline, preview-mode contract.
- The target scene's existing `base.html`, `base.css`, `base.js` (for CSS-selector targets like `#btn-continue`).

## Operating checklist

1. **Restate the idea** in one paragraph: subject, mood, beats, target devices.
2. **Storyboard** 3–5 beats with approximate timeline fractions (0.0–1.0).
3. **List layers**: id, type (`image` / `div` / `text` / `svg`), assets or HTML, `z`, `initial`, `parallax` if needed.
4. **List verses** (if any): id, text, style, position.
5. **Draft `timeline:`** cue-by-cue using only v1 kinds: `set`, `show`, `hide`, `move`, `zoom`, `fade`, `pause`.
6. **Prefer responsive units** (`vw`, `vh`, `%`) for positions and scales.
7. **Add parallax** on background/foreground layers for depth where appropriate.
8. **Add `mobile:` block** when portrait needs different layout, length, parallax, or movement; use per-cue `device:` for direction changes; use `mobile.timeline:` only when choreography is fundamentally different.
9. **Validate** against the cue catalogue — no unknown kinds; every cue has `target`, `at`, `kind`; `at`/`to` in 0..1.
10. **Bootstrap** `base.html` with `<main id="demo-root">` and optional static controls; `base.js` calls `Demo.run(window.__DEMO__)`.

## Output contract

Deliver:

- `playground/worlds_content/<world>/scenes/<scene>/demo.yaml` (required)
- Updated or minimal `base.{html,css,js}` if the scene is new
- Optional files under `scenes/<scene>/assets/` (or document paths for the user to add art later)

Wire new scenes in `world.yaml` (`scene_versions`, `navigation`, `public_scenes` if needed) — or hand off to Developer.

## Hand-off

- **To Ethics Reviewer** before user-visible demo copy goes live in an experiment.
- **To Tester** to walk the demo on desktop and mobile widths; verify hidden scrollbar, progress bar, scroll scrub.
- **To Scene/UI Designer** if the demo needs substantial custom CSS beyond SDK defaults.
- **To Developer** if a needed cue kind does not exist in the catalogue — never invent kinds.

## Footguns

- Do not edit `playground/static/sdk/demo.js` or `demo.css`.
- Do not invent cue kinds or layer options not documented in `demo_framework.md`.
- `hide` direction uses `exit:` (not `to:` — `to` is the timeline end fraction).
- Cues animate whole elements; for staggered text use verses + `text_reveal` on `show`.
- Demo scenes require real scroll — the SDK adds `pg-scene--scroll pg-scene--demo`; do not fight this in scene CSS.
- Asset paths use `assets/filename.ext`; served under `/worlds/<w>/scenes/<s>/assets/`.

## Reference fixture

See [`playground/worlds_content/_fixtures/scenes/smoke/demo.yaml`](../../playground/worlds_content/_fixtures/scenes/smoke/demo.yaml) for a minimal example covering every v1 cue kind.
