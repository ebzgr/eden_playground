"""Unit tests for the new patch op set (lxml + CSS selectors)."""

from pathlib import Path

import pytest

from playground.services.world_builder.patcher import resolve_version


def _make_version(tmp_path: Path, vid: str, manifest_body: str) -> Path:
    scene_dir = tmp_path / "scene"
    (scene_dir / "versions").mkdir(parents=True, exist_ok=True)
    (scene_dir / "versions" / f"{vid}.yaml").write_text(manifest_body)
    return scene_dir


def test_set_text_replaces_inner_text(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        'patches:\n'
        '  - { op: setText, selector: "#cta", value: "Hurry!" }\n',
    )
    spec = resolve_version(scene_dir, "v1", '<button id="cta">Go</button>', "", "", {})
    assert "Hurry!" in spec.html
    assert "Go" not in spec.html


def test_add_and_remove_class(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        'patches:\n'
        '  - { op: addClass, selector: ".btn", value: "urgent" }\n'
        '  - { op: removeClass, selector: ".btn", value: "muted" }\n',
    )
    spec = resolve_version(
        scene_dir,
        "v1",
        '<a class="btn muted">x</a>',
        "",
        "",
        {},
    )
    assert "urgent" in spec.html
    assert "muted" not in spec.html


def test_set_and_remove_attr(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        'patches:\n'
        '  - { op: setAttr,    selector: "#cta", name: "data-variant", value: "B" }\n'
        '  - { op: removeAttr, selector: "#cta", name: "disabled" }\n',
    )
    spec = resolve_version(
        scene_dir, "v1", '<button id="cta" disabled>X</button>', "", "", {}
    )
    assert 'data-variant="B"' in spec.html
    assert "disabled" not in spec.html


def test_insert_before_after_and_remove(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        'patches:\n'
        '  - { op: insertBefore, selector: "#mid", html: "<p id=\\"a\\">A</p>" }\n'
        '  - { op: insertAfter,  selector: "#mid", html: "<p id=\\"b\\">B</p>" }\n'
        '  - { op: remove,       selector: "#trash" }\n',
    )
    base = (
        '<div>'
        '<span id="trash">junk</span>'
        '<span id="mid">M</span>'
        '</div>'
    )
    spec = resolve_version(scene_dir, "v1", base, "", "", {})
    assert "junk" not in spec.html
    # Order: A, M, B
    a = spec.html.index('id="a"')
    m = spec.html.index('id="mid"')
    b = spec.html.index('id="b"')
    assert a < m < b


def test_append_and_prepend_inside(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        'patches:\n'
        '  - { op: appendInside,  selector: "ul", html: "<li>last</li>" }\n'
        '  - { op: prependInside, selector: "ul", html: "<li>first</li>" }\n',
    )
    spec = resolve_version(scene_dir, "v1", "<ul><li>mid</li></ul>", "", "", {})
    first = spec.html.index("first")
    mid = spec.html.index("mid")
    last = spec.html.index("last")
    assert first < mid < last


def test_set_html_replaces_inner_html(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        'patches:\n'
        '  - { op: setHtml, selector: "#box", value: "<strong>new</strong>" }\n',
    )
    spec = resolve_version(scene_dir, "v1", '<div id="box">old</div>', "", "", {})
    assert "<strong>new</strong>" in spec.html
    assert "old" not in spec.html


def test_unknown_op_is_ignored(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        'patches:\n'
        '  - { op: explodePlanet, selector: "#x" }\n'
        '  - { op: setText, selector: "#x", value: "ok" }\n',
    )
    spec = resolve_version(scene_dir, "v1", '<p id="x">hi</p>', "", "", {})
    assert "ok" in spec.html


def test_nav_overrides_merge(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        "nav_overrides:\n"
        "  cta_click: variant_next\n"
        "  on:back: variant_back\n",
    )
    spec = resolve_version(
        scene_dir, "v1", "<p/>", "", "", {"on:cta_click": "default_next"}
    )
    assert spec.nav_overrides["on:cta_click"] == "variant_next"
    assert spec.nav_overrides["on:back"] == "variant_back"


def test_css_and_js_append_after_base(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        "css_append: '.x { color: red; }'\n"
        "js_append: 'console.log(\"v1\");'\n",
    )
    spec = resolve_version(scene_dir, "v1", "<p/>", "/* base css */", "/* base js */", {})
    assert "base css" in spec.css and "color: red" in spec.css
    assert "base js" in spec.js and "console.log" in spec.js


def test_full_html_field_replaces_base(tmp_path):
    scene_dir = _make_version(
        tmp_path,
        "v1",
        "html: '<main id=\"v\">NEW</main>'\n"
        "css: 'body { color: red; }'\n",
    )
    spec = resolve_version(scene_dir, "v1", "<main>OLD</main>", "/* base */", "", {})
    assert "NEW" in spec.html and "OLD" not in spec.html
    assert spec.css == "body { color: red; }"  # full replacement, not append
