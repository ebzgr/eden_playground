"""HTML shell for scene view / admin preview."""

from __future__ import annotations

import json

from playground.schemas.world import SceneResolved

# Injected before every scene's CSS. Player scenes fill the viewport with no
# document scroll unless the scene adds body.pg-scene--scroll (opt-in).
SCENE_SHELL_CSS = """
html {
  height: 100%;
  overflow: hidden;
}
body.pg-scene {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
  box-sizing: border-box;
}
body.pg-scene > main {
  box-sizing: border-box;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  margin: 0;
}
body.pg-scene[data-preview="true"] > main {
  padding-top: 2.25rem;
  max-height: 100%;
}
body.pg-scene.pg-scene--scroll {
  overflow: auto;
  overflow-x: hidden;
}
body.pg-scene.pg-scene--scroll > main {
  height: auto;
  min-height: 100%;
  max-height: none;
  overflow: visible;
}
"""

PREVIEW_BANNER_CSS = """
.pg-preview-banner {
  position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
  padding: 0.45rem 1rem; font: 600 0.75rem/1.4 system-ui, sans-serif;
  text-align: center; color: #1a1028;
  background: linear-gradient(90deg, #ffe08a, #ffc857);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
"""


def _experiment_context(arms: dict | None) -> dict | None:
    if not arms:
        return None
    exp_id, meta = next(iter(arms.items()))
    if not isinstance(meta, dict):
        return {"id": exp_id, "armId": meta, "assignmentScope": None}
    return {
        "id": exp_id,
        "armId": meta.get("arm_id"),
        "assignmentScope": meta.get("assignment_scope"),
    }


def render_scene_page(
    resolved: SceneResolved,
    *,
    preview_mode: bool = False,
) -> str:
    w, s = resolved.world_id, resolved.scene_id
    session = resolved.session_id or ""
    experiment = _experiment_context(resolved.experiment_arms)
    pg_config = {
        "apiBase": "",
        "worldId": w,
        "sceneId": s,
        "sessionId": session,
        "versionId": resolved.version_id,
        "experiment": experiment,
        "experimentArms": resolved.experiment_arms,
        "nav": resolved.nav,
        "previewMode": preview_mode,
    }
    config_json = json.dumps(pg_config)
    preview_banner = ""
    if preview_mode:
        preview_banner = (
            '<div class="pg-preview-banner" role="status">'
            "Admin preview — events and consent are not recorded."
            "</div>"
        )
        css = SCENE_SHELL_CSS + PREVIEW_BANNER_CSS + resolved.css
    else:
        css = SCENE_SHELL_CSS + resolved.css

    is_demo = resolved.demo_config is not None
    demo_config_json = json.dumps(resolved.demo_config) if is_demo else ""
    body_classes = "pg-scene"
    if is_demo:
        body_classes += " pg-scene--scroll pg-scene--demo"
    html_class = ' class="pg-scene--demo"' if is_demo else ""

    demo_head = ""
    demo_scripts = ""
    if is_demo:
        demo_head = '<link rel="stylesheet" href="/static/sdk/demo.css"/>'
        demo_scripts = f"""<script>window.__DEMO__ = {demo_config_json};</script>
<script src="/static/vendor/gsap.min.js"></script>
<script src="/static/vendor/ScrollTrigger.min.js"></script>
<script src="/static/sdk/demo.js"></script>"""

    demo_attr = ' data-demo="true"' if is_demo else ""

    # GSAP for map_world scenes that animate in scene JS (must run before inline base.js).
    vendor_gsap = ""
    if w == "map_world" and s == "map":
        vendor_gsap = '<script src="/static/vendor/gsap.min.js"></script>\n'

    return f"""<!DOCTYPE html>
<html lang="en"{html_class}><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{w} / {s}{" (preview)" if preview_mode else ""}</title>
{demo_head}
<style>{css}</style>
</head><body class="{body_classes}" data-world="{w}" data-scene="{s}" data-version="{resolved.version_id}" data-session="{session}" data-preview="{str(preview_mode).lower()}"{demo_attr}>
{preview_banner}
{resolved.html}
<script>window.__PLAYGROUND__ = {config_json};</script>
<script src="/static/sdk/playground.js"></script>
<script src="/static/sdk/tracker.js"></script>
<script src="/static/sdk/events.js"></script>
{demo_scripts}
{vendor_gsap}<script>{resolved.js}</script>
</body></html>"""
