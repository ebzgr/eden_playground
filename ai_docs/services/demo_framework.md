# Service: demo_framework

## What this service does

YAML-driven scroll-scrubbed demos for player scenes. A scene becomes a **demo scene** when its directory contains `demo.yaml`. The runtime loads GSAP + ScrollTrigger and `playground/static/sdk/demo.js`, which builds layers, verses, and a pinned timeline controlled by scroll (scrub forward / reverse on scroll up).

Real narrative demos are authored later by humans or the **demo_builder** role. v1 ships the SDK plus a `_fixtures/smoke` test scene.

## Key files

- [`playground/services/world_builder/demo_config.py`](../../playground/services/world_builder/demo_config.py) — load/validate `demo.yaml`, mobile merge, device filter.
- [`playground/static/sdk/demo.js`](../../playground/static/sdk/demo.js) — `Demo.run(config, options)`.
- [`playground/static/sdk/demo.css`](../../playground/static/sdk/demo.css) — demo layout, hidden scrollbar, progress bar.
- [`playground/static/vendor/`](../../playground/static/vendor/) — vendored GSAP + ScrollTrigger.
- [`playground/services/world_builder/render.py`](../../playground/services/world_builder/render.py) — injects demo assets when `SceneResolved.demo_config` is set.

## Scene type contract

| Condition | Behavior |
|---|---|
| `<scene>/demo.yaml` exists | Demo scene: inject `demo.css`, GSAP, ScrollTrigger, `demo.js`, `window.__DEMO__`, body classes `pg-scene--scroll pg-scene--demo` |
| No `demo.yaml` | Normal scene — unchanged HTML shell |

## `demo.yaml` top-level options

| Field | Type | Default | Description |
|---|---|---|---|
| `length` | int | 2000 | Virtual scroll length in px (ScrollTrigger `end: +=length`) |
| `scrub` | bool \| number | 1.5 | ScrollTrigger scrub. Higher = more inertia/smoothing. Numeric is the linger seconds. |
| `pin` | bool | true | Pin `.demo-stage` while scrolling |
| `default_ease` | string | `power2.inOut` | Default GSAP ease for cues |
| `progress_bar` | bool | true | Slim 2px top progress bar |
| `background` | object | — | `{ type: gradient, value: "<css>" }` on stage |
| `layers` | list | [] | Visual layers (see below) |
| `verses` | list | [] | Poem / title text overlays |
| `timeline` | list | [] | Cue list (see catalogue) |
| `mobile` | object | — | Overrides when viewport ≤ `max_width` |

## Layer types

| `type` | Fields | Renders |
|---|---|---|
| `image` | `src`, `alt`, `class`, `style` | `<img>` |
| `div` | `html`, `class`, `style` | `<div>` with arbitrary HTML (e.g. `<p>` inside) |
| `text` | `text`, `class`, `style` | Styled `<p>` shortcut |
| `svg` | `html` | Inline SVG |

Common layer fields: `id`, `z`, `anchor` (`center`, `top`, `bottom`, …), `initial: { x, y, scale, rotation, opacity, z }`, `parallax`.

### Parallax

```yaml
parallax: 0.5                  # y-axis shorthand
parallax: { y: 0.5, x: -0.2 }  # explicit axes
```

Factor semantics: `1.0` = scroll lockstep; `<1.0` = slower (background); `>1.0` = faster (foreground); negative = counter-drift. Parallax applies to a wrapper; cues animate the inner element — both stack.

Position units: prefer `%`, `vw`, `vh` for responsive layouts.

## Verses

```yaml
verses:
  - id: v1
    text: "From silence, a song begins."
    style: title | poem | caption | none
    position: top | center | bottom | { x, y }
```

Hidden by default (autoAlpha 0); revealed with a `show` cue, or made visible at scroll 0 via `set { autoAlpha: 1 }`. Optional `text_reveal: words | chars` and `stagger` on the cue.

**Positioning.** `position: center` (the default) anchors the verse with `left: 50%; top: 50%` and uses GSAP `xPercent: -50; yPercent: -50` for centering — so later `y` tweens (e.g. `y: "30vh"`) stack on top of the centering offset instead of overwriting it. `top` and `bottom` keep horizontal centering and pin vertically at 12%. Object form `{ x, y }` accepts raw CSS values and skips auto-centering.

### Vertical scroll-through pattern

Common "reading a long letter" effect — each verse rises from below to above, with overlapping fades:

```yaml
- { target: c01, at: 0.05,  kind: set,  props: { y: "30vh" } }     # start at ~80% from top
- { target: c01, at: 0.05,  to: 0.059, kind: show, from: none }    # fade in (autoAlpha 0→1)
- { target: c01, at: 0.05,  to: 0.125, kind: move, props: { y: "-30vh" } }  # rise across range
- { target: c01, at: 0.116, to: 0.125, kind: hide, exit: none }    # fade out near top
```

Cadence < range gives simultaneous-visibility overlap so the next verse is fully in before the current starts leaving.

## Cue catalogue (v1)

Each cue: `target`, `at` (0..1), `to` (0..1, default `at`), `kind`, optional `ease`, optional `device: all | desktop | mobile`.

| Kind | Options | Effect |
|---|---|---|
| `set` | `props: { x, y, scale, rotation, opacity, autoAlpha, xPercent, yPercent, z }` | Instant (reversible) set at `at`. `autoAlpha` toggles opacity + visibility together. Values accept GSAP units (`"30vh"`, `"50%"`). |
| `show` | `from: up\|down\|left\|right\|none`; verses: `text_reveal`, `stagger` | Fade in via `autoAlpha`. With `from: none`, **does not touch `x`/`y`** — useful when a preceding `set` placed the element at a custom position. With a direction, `x`/`y` slide back to `0`. |
| `hide` | `exit: up\|down\|left\|right\|none` | Fade out via `autoAlpha`. With `exit: none`, does not touch `x`/`y`. |
| `move` | `props: { x, y }` | Animate position; accepts unit strings (`"30vh"`). |
| `zoom` | `props: { scale }` | Animate scale |
| `fade` | `props: { opacity }` | Animate opacity (no visibility flip; use `hide` for autoAlpha) |
| `pause` | — | Hold timeline between `at` and `to` |

### Target resolution

- **Layer id** — e.g. `target: gaia`
- **Verse id** — e.g. `target: v1`
- **CSS selector** — e.g. `target: "#btn-continue"` (element in scene `base.html`)

## Mobile / responsive

Three tools (same file):

1. **Responsive units** (`vw`, `vh`, `%`) — default; handles most cases.
2. **Per-cue `device:`** — different movement on desktop vs mobile:

   ```yaml
   - { target: b, at: 0.4, to: 0.8, kind: move, props: { x: "50%" }, device: desktop }
   - { target: b, at: 0.4, to: 0.8, kind: move, props: { y: "20%" }, device: mobile }
   ```

3. **`mobile:` block** — deep-merge layers, override `length`, etc.; optional **`mobile.timeline:`** fully replaces desktop timeline:

   ```yaml
   mobile:
     max_width: 768
     length: 1800
     layers:
       gaia:
         initial: { scale: 0.5 }
     timeline:
       - { target: gaia, at: 0.0, to: 1.0, kind: show }
   ```

## Scene bootstrap (`base.js`)

Minimal demo scene JS:

```js
(function () {
  if (window.Demo && window.__DEMO__) {
    window.Demo.run(window.__DEMO__, {
      onComplete: function () {
        var btn = document.getElementById("btn-continue");
        if (btn) btn.classList.add("ready");
      },
    });
  }
})();
```

## Assets

Place files under `scenes/<scene>/assets/`. Served at:

`/worlds/<world_id>/scenes/<scene_id>/assets/<path>`

Reference in layers: `src: assets/gaia.svg` (resolved relative to the assets route).

## Cookbook snippets

### Layer appears, moves, disappears

```yaml
timeline:
  - { target: hero, at: 0.0, to: 0.2, kind: show, from: up }
  - { target: hero, at: 0.2, to: 0.6, kind: move, props: { x: "30%" } }
  - { target: hero, at: 0.7, to: 0.9, kind: hide, exit: down }
```

### Depth parallax background

```yaml
layers:
  - id: sky
    type: div
    class: bg-sky
    parallax: 0.3
    z: 0
```

### Verse word reveal

```yaml
timeline:
  - { target: v1, at: 0.1, to: 0.35, kind: show, text_reveal: words, stagger: 0.06 }
```

### Reveal Continue button from base.html

```yaml
timeline:
  - { target: "#btn-continue", at: 0.92, to: 1.0, kind: show }
```

## Scroll container (scene shell)

The default scene shell sets `html { overflow: hidden }`. Demo scenes must scroll on **`html`**, not `body`, because ScrollTrigger tracks the window scroll by default. `demo.css` overrides this for `html.pg-scene--demo` (`overflow-y: auto` on `html`, `overflow: visible` on `body`). `demo.js` also passes `scroller: document.scrollingElement` to ScrollTrigger so the contract is asserted in code, not only in CSS. Without that pairing, wheel/trackpad input moves `body` but the timeline never advances — the stage stays dark with every verse word stuck at `opacity: 0`.

## Scroll smoothness

On first demo init, `demo.js` calls `ScrollTrigger.normalizeScroll(true)` and `ScrollTrigger.config({ ignoreMobileResize: true })` (idempotent — guarded by a global flag). Combined with the default `scrub: 1.5`, this gives a smoother cross-browser feel without an extra smooth-scroll library. Demo scenes can override `scrub` per-demo in `demo.yaml`. For a stronger pre-baked smoothness, bump to `scrub: 2` or higher; for a strict 1:1 mapping use `scrub: true`.

Demo backgrounds should also paint `html` and `body` directly (e.g. `html.pg-scene--demo, body.pg-scene--demo { background: #06060f; }`). The pinned stage covers the viewport during the scroll range, but the underlying page is briefly visible at the very end of the scroll once the pin releases; matching the body color prevents a white flash.

## Reversibility contract

Cues must reverse cleanly when the user scrolls back up (scrub is bidirectional). The SDK uses GSAP's `autoAlpha` (opacity + visibility together) and `tl.set` / `tl.fromTo` exclusively — never `tl.add(callback)` to flip visibility, and never `onComplete` to hide elements. If you add a new cue kind, follow the same rule: every state change must live inside a tween (or `tl.set`) so a backward scrub can undo it.

## Test fixture

[`playground/worlds_content/_fixtures/scenes/smoke/`](../../playground/worlds_content/_fixtures/scenes/smoke/) — not user-facing; exercises every cue kind. View at `/worlds/_fixtures/scenes/smoke/view` (public).

## Python API

```python
from playground.services.world_builder.demo_config import (
    load_demo_yaml,
    validate_demo_config,
    resolve_demo_config_for_device,
    filter_timeline_by_device,
    DemoCueKind,
)
```

`SceneResolved.demo_config` is populated by `resolve_scene` / `resolve_scene_guest` when `demo.yaml` exists.
