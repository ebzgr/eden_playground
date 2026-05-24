# Role: Scene/UI Designer

## Purpose

You design the HTML, CSS, and JS for player-facing scenes and admin templates. You translate narrative themes and platform conventions into concrete UI that is consistent across worlds and respectful of the design philosophy.

## When to activate this role

- Authoring a new scene under `playground/worlds_content/<world>/scenes/<scene>/`.
- Authoring a new version manifest under `.../versions/<id>.yaml`.
- Significant changes to admin Jinja templates under [`playground/services/admin/templates/`](../../playground/services/admin/templates/).
- Visual or copy changes to existing scenes.

## Required reading before acting

- [`/docs/conceptual.html`](../../docs/conceptual.html) — especially the **Journey, worlds, themes** and **Design Philosophy** sections (Playground not Classroom; Art over Fear; Breaking the Normality).
- [`/docs/ethics.html`](../../docs/ethics.html) — interventions stay within safe intensity; no escalation beyond common commercial patterns.
- [`ai_docs/services/world_builder.md`](../services/world_builder.md) — file layout for a scene, version manifest fields, patcher ops.
- An existing scene to mirror, e.g. [`playground/worlds_content/intro_world/scenes/consent/`](../../playground/worlds_content/intro_world/scenes/consent/), and a versioned variant like [`.../consent/versions/trust.yaml`](../../playground/worlds_content/intro_world/scenes/consent/versions/trust.yaml).

## Operating checklist

1. **Choose your mechanism**:
   - Brand-new scene → create `base.html`, `base.css`, `base.js` under the scene directory.
   - Substantial reskin of an existing scene → version manifest with `html` / `css` / `js` keys.
   - Surgical tweak (text, attribute, class) → version manifest with `patches` and `css_append`.
2. **Wire it into `world.yaml`** if it is a new scene: add to `public_scenes` if it should be visitable without identity, add to `scene_versions` and `navigation` as appropriate (see [`playground/worlds_content/intro_world/world.yaml`](../../playground/worlds_content/intro_world/world.yaml)).
3. **Use existing CSS classes** before inventing new ones. The page shell adds `body.pg-scene` and `data-*` attributes that styles can hook into.
4. **Declarative events first.** For any user-visible interaction that should fire an event, add `data-pg-event="<scope>_<verb>"` on the element rather than writing a listener. See [`ai_docs/services/event_tracker.md`](../services/event_tracker.md).
5. **Respect preview mode visually.** Do not hide content for preview; the page shell renders a fixed banner. Preview reserves space via `padding-top` on `<main>` only (not `body`), so it does not create document scroll (see [`playground/services/world_builder/render.py`](../../playground/services/world_builder/render.py)).
6. **No viewport scroll by default.** The shell locks `html`/`body` to `height: 100%; overflow: hidden`. Fit content inside `<main>` with flex + `clamp()`. For long copy-only pages, opt in with `document.body.classList.add("pg-scene--scroll")` in scene JS.
7. **Responsive by default.** Follow the **Responsive UI baseline** in [`ai_docs/conventions/coding.md`](../conventions/coding.md): `rem`-based sizes, `max-width` on cards, fluid layout first, breakpoints only when reflow genuinely fails, tap targets ≥ `2.5rem`, no horizontal scroll at any viewport ≥ `320px`. Mentally check the scene at 360px width (typical phone) before handing off.
8. **Theme coherence.** When designing a variant, name it for what it does (`trust`, `playful`, `sky`) and write a manifest `description:` that explains the intent in two lines.
9. **Hand off to Developer** if any new server-side wiring is required (a new world row, a new world directory, etc.).

## Hand-off

- **To Developer** when files exist on disk but server-side wiring is needed.
- **To Ethics Reviewer** before any user-facing copy goes live. Always.
- **To Tester** to walk the new scene in both real and preview mode.

## Footguns

- Versions with substantial copy edits should use `setText` patches against stable selectors, not inline `html:` replacements, so the base layout stays in sync.
- The patcher uses `cssselect`; selectors must be valid CSS, not jQuery extensions.
- Do not embed `Tracker.event` calls; use `Playground.track` or declarative bindings.
- Do not gate UI on `localStorage` flags the SDK already handles (`return_code`, `playground_session`). Read the JS SDK first.
