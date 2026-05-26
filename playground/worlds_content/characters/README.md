# Character assets

Shared portraits and sprites for narrative characters. Use this folder so art can be reused across worlds and scenes.

## Layout

```
characters/
  <character_id>/
    portrait.png    # default bust / full portrait
    …               # optional: expression-*.png, sprite-*.png, etc.
```

## URLs

Files are served at:

```
/worlds/characters/<character_id>/<filename>
```

Example — Gaia portrait in the welcome scene:

```html
<img src="/worlds/characters/gaia/portrait.png" alt="Gaia" />
```

## Adding a character

1. Create `characters/<character_id>/` (lowercase id, e.g. `gaia`, `mentor`).
2. Drop image files there (PNG/WebP/SVG).
3. Reference the URL above from any scene `base.html` or version manifest `html` block.

Scene-local assets remain under `worlds/<world>/scenes/<scene>/assets/` when art is used in one scene only.
