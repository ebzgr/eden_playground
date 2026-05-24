"""Demo SDK config loading, mobile merge, and render injection."""

from pathlib import Path

import pytest
import yaml

from playground.schemas.world import SceneResolved
from playground.services.world_builder.demo_config import (
    DEMO_CUE_KINDS,
    DemoCueKind,
    filter_timeline_by_device,
    load_demo_yaml,
    resolve_demo_config_for_device,
    validate_demo_config,
)
from playground.services.world_builder.render import render_scene_page
from playground.services.world_builder.service import resolve_scene_guest

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "demo_smoke"


def test_cue_catalogue_matches_python_enum():
    assert set(DemoCueKind) == DEMO_CUE_KINDS


def test_validate_rejects_unknown_kind():
    with pytest.raises(ValueError, match="unknown cue kind"):
        validate_demo_config({"timeline": [{"kind": "explode", "at": 0}]})


def test_load_demo_yaml_for_fixture_world():
    cfg = load_demo_yaml("_fixtures", "smoke")
    assert cfg is not None
    assert cfg["length"] == 1200
    assert len(cfg["timeline"]) >= 7


def test_load_demo_yaml_none_when_missing():
    assert load_demo_yaml("intro_world", "lab") is None


def test_filter_timeline_by_device():
    timeline = [
        {"kind": "show", "device": "all"},
        {"kind": "move", "device": "desktop"},
        {"kind": "move", "device": "mobile"},
    ]
    desktop = filter_timeline_by_device(timeline, device="desktop")
    assert len(desktop) == 2
    mobile = filter_timeline_by_device(timeline, device="mobile")
    assert len(mobile) == 2


def test_mobile_merge_layers_and_length():
    cfg = load_demo_yaml("_fixtures", "smoke")
    merged = resolve_demo_config_for_device(cfg, is_mobile=True)
    assert merged["length"] == 900
    layers = {layer["id"]: layer for layer in merged["layers"]}
    assert layers["a"]["initial"]["scale"] == 0.4
    assert layers["b"]["parallax"] == 0.2


def test_mobile_timeline_replacement():
    raw = yaml.safe_load((FIXTURES / "mobile_timeline.yaml").read_text(encoding="utf-8"))
    merged = resolve_demo_config_for_device(raw, is_mobile=True)
    assert len(merged["timeline"]) == 1
    assert merged["timeline"][0]["kind"] == "zoom"


@pytest.mark.asyncio
async def test_render_injects_demo_assets():
    resolved = await resolve_scene_guest("_fixtures", "smoke")
    html = render_scene_page(resolved)
    assert resolved.demo_config is not None
    assert "window.__DEMO__" in html
    assert "/static/vendor/gsap.min.js" in html
    assert "/static/vendor/ScrollTrigger.min.js" in html
    assert "/static/sdk/demo.js" in html
    assert "/static/sdk/demo.css" in html
    assert 'class="pg-scene pg-scene--scroll pg-scene--demo"' in html
    assert 'data-demo="true"' in html


@pytest.mark.asyncio
async def test_non_demo_scene_regression_html():
    """Demo framework must not auto-inject its trio for non-demo scenes.

    A non-demo scene may still load GSAP itself (lab does, for its scramble
    effect), so we don't check for vendor/gsap.min.js here — that is the
    scene's choice. We assert only that the *demo SDK* pipeline did not run.
    """
    resolved = await resolve_scene_guest("intro_world", "lab")
    html = render_scene_page(resolved)
    assert resolved.demo_config is None
    assert "window.__DEMO__" not in html
    assert "/static/sdk/demo.js" not in html
    assert "/static/sdk/demo.css" not in html
    assert "/static/vendor/ScrollTrigger.min.js" not in html
    assert "pg-scene--demo" not in html
    assert 'class="pg-scene"' in html
    assert "Marketing for Betterment Lab" in html


def test_render_non_demo_minimal_snapshot():
    """Stable shell markers for non-demo scenes (no demo SDK injection)."""
    resolved = SceneResolved(
        world_id="intro_world",
        scene_id="lab",
        version_id="base",
        html="<main>Lab</main>",
        css="",
        js="// lab",
        nav={},
        demo_config=None,
    )
    html = render_scene_page(resolved)
    assert html.count("<script") == 5
    assert "pg-scene--demo" not in html
    assert "/static/sdk/demo.js" not in html
