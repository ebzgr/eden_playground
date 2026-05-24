"""Versioning resolver tests (single YAML manifest per version)."""

import textwrap
from pathlib import Path

import pytest

from playground.services.world_builder.patcher import (
    discover_versions,
    resolve_version,
)


def _scene(tmp_path: Path) -> Path:
    scene_dir = tmp_path / "scene"
    (scene_dir / "versions").mkdir(parents=True)
    return scene_dir


def _manifest(scene_dir: Path, vid: str, body: str) -> None:
    (scene_dir / "versions" / f"{vid}.yaml").write_text(textwrap.dedent(body))


def test_base_returns_unmodified(tmp_path):
    scene_dir = _scene(tmp_path)
    spec = resolve_version(scene_dir, "base", "<h1>hi</h1>", "css", "js", {})
    assert spec.html == "<h1>hi</h1>"
    assert spec.mode == "base"


def test_full_html_and_css_replace_base(tmp_path):
    scene_dir = _scene(tmp_path)
    _manifest(
        scene_dir,
        "v_sky",
        """
        id: v_sky
        html: |
          <main>SKY</main>
        css: |
          body { background: blue; }
        """,
    )
    spec = resolve_version(
        scene_dir, "v_sky", "<main>BASE</main>", "css-base", "js-base", {}
    )
    assert "SKY" in spec.html
    assert "BASE" not in spec.html
    assert "background: blue" in spec.css
    assert spec.js == "js-base"  # absent → base
    assert spec.mode == "manifest"


def test_patches_and_css_append(tmp_path):
    scene_dir = _scene(tmp_path)
    _manifest(
        scene_dir,
        "v_tweak",
        """
        id: v_tweak
        patches:
          - { op: setText, selector: "#cta", value: "Click!" }
        css_append: |
          #cta { color: red; }
        """,
    )
    spec = resolve_version(
        scene_dir, "v_tweak", '<button id="cta">old</button>', "/* base */", "", {}
    )
    assert "Click!" in spec.html
    assert "base" in spec.css and "color: red" in spec.css


def test_full_html_then_patches(tmp_path):
    scene_dir = _scene(tmp_path)
    _manifest(
        scene_dir,
        "v_both",
        """
        id: v_both
        html: '<main><button id="cta">go</button></main>'
        patches:
          - { op: addClass, selector: "#cta", value: "skin" }
        """,
    )
    spec = resolve_version(scene_dir, "v_both", "<main>BASE</main>", "", "", {})
    assert "BASE" not in spec.html
    assert 'class="skin"' in spec.html
    assert spec.mode == "manifest"


def test_unknown_version_falls_back_to_base(tmp_path):
    scene_dir = _scene(tmp_path)
    spec = resolve_version(scene_dir, "missing", "BASE", "CSS", "JS", {})
    assert spec.html == "BASE"
    assert spec.id == "base"


def test_discover_versions_lists_yaml_only(tmp_path):
    scene_dir = _scene(tmp_path)
    _manifest(scene_dir, "v_one", "id: v_one\n")
    _manifest(scene_dir, "v_two", "id: v_two\n")
    (scene_dir / "versions" / "stray.json").write_text("{}")
    (scene_dir / "versions" / "old_layout").mkdir()
    assert discover_versions(scene_dir) == ["v_one", "v_two"]


@pytest.mark.asyncio
async def test_view_force_version_renders_trust(client):
    r = await client.get(
        "/worlds/intro_world/scenes/consent/view?force_version=trust"
    )
    assert r.status_code == 200
    assert b"Your privacy comes first" in r.content


@pytest.mark.asyncio
async def test_view_force_version_renders_playful(client):
    r = await client.get(
        "/worlds/intro_world/scenes/consent/view?force_version=playful"
    )
    assert r.status_code == 200
    assert b"The Tiny Print" in r.content
    assert b"Let's get curious" in r.content
