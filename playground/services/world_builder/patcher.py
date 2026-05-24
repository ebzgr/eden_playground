"""Resolve scene version content from a single YAML manifest per version.

Layout (one file per version):

  scenes/<scene_id>/versions/
    <version_id>.yaml      manifest — the only file a version needs

Manifest fields (all optional except `id` defaulting to file stem):

  id:             version identifier (defaults to filename stem)
  description:    free text
  html:           full HTML for this version (replaces base.html when present)
  css:            full CSS for this version (replaces base.css when present)
  js:             full JS for this version (replaces base.js when present)
  css_append:     appended after the resolved CSS
  js_append:      appended after the resolved JS
  patches:        list of DOM ops (see PATCH_OPS) applied to the resolved HTML
  nav_overrides:  {event: next_scene} merged into the scene's default nav

Use `html` / `css` / `js` for substantial reskins; use `patches` + `css_append`
for surgical tweaks. The two can be combined.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml
from lxml import etree, html as lxml_html


PATCH_OPS: tuple[str, ...] = (
    "setText",
    "setHtml",
    "setAttr",
    "removeAttr",
    "addClass",
    "removeClass",
    "appendInside",
    "prependInside",
    "insertBefore",
    "insertAfter",
    "remove",
)


@dataclass
class VersionSpec:
    """Materialized version: what the renderer ships to the browser."""

    id: str
    html: str
    css: str
    js: str
    nav_overrides: dict[str, str] = field(default_factory=dict)
    description: str | None = None
    mode: str = "base"  # base | manifest


# --- Selector & DOM helpers ----------------------------------------------

_FRAGMENT_WRAPPER = "div"


def _parse_fragment(s: str):
    """Parse an HTML fragment into a wrapper element we can serialise back."""
    return lxml_html.fragment_fromstring(s, create_parent=_FRAGMENT_WRAPPER)


def _serialise_fragment(root) -> str:
    out = etree.tostring(root, encoding="unicode", method="html")
    open_tag = f"<{_FRAGMENT_WRAPPER}>"
    close_tag = f"</{_FRAGMENT_WRAPPER}>"
    if out.startswith(open_tag) and out.endswith(close_tag):
        return out[len(open_tag) : -len(close_tag)]
    return out


def _select(root, selector: str) -> list:
    if not selector:
        return []
    try:
        return root.cssselect(selector)
    except Exception:
        return []


def _parse_children(snippet: str) -> list:
    wrapper = _parse_fragment(snippet)
    return list(wrapper)


def _replace_inner(el, snippet: str) -> None:
    el.text = None
    for child in list(el):
        el.remove(child)
    wrapper = _parse_fragment(snippet)
    el.text = wrapper.text
    for child in list(wrapper):
        el.append(child)


# --- Patch op implementations --------------------------------------------

def _op_set_text(el, p: dict) -> None:
    for child in list(el):
        el.remove(child)
    el.text = str(p.get("value", ""))


def _op_set_html(el, p: dict) -> None:
    _replace_inner(el, str(p.get("value", p.get("html", ""))))


def _op_set_attr(el, p: dict) -> None:
    name = p.get("name")
    if not name:
        return
    el.set(name, str(p.get("value", "")))


def _op_remove_attr(el, p: dict) -> None:
    name = p.get("name")
    if name and name in el.attrib:
        del el.attrib[name]


def _op_add_class(el, p: dict) -> None:
    cls = str(p.get("value", "")).strip()
    if not cls:
        return
    existing = (el.get("class") or "").split()
    if cls not in existing:
        existing.append(cls)
        el.set("class", " ".join(existing))


def _op_remove_class(el, p: dict) -> None:
    cls = str(p.get("value", "")).strip()
    if not cls:
        return
    existing = (el.get("class") or "").split()
    filtered = [c for c in existing if c != cls]
    if filtered:
        el.set("class", " ".join(filtered))
    elif "class" in el.attrib:
        del el.attrib["class"]


def _op_append_inside(el, p: dict) -> None:
    for child in _parse_children(str(p.get("html", p.get("value", "")))):
        el.append(child)


def _op_prepend_inside(el, p: dict) -> None:
    children = _parse_children(str(p.get("html", p.get("value", ""))))
    for i, child in enumerate(children):
        el.insert(i, child)


def _op_insert_before(el, p: dict) -> None:
    parent = el.getparent()
    if parent is None:
        return
    idx = list(parent).index(el)
    for offset, child in enumerate(_parse_children(str(p.get("html", p.get("value", ""))))):
        parent.insert(idx + offset, child)


def _op_insert_after(el, p: dict) -> None:
    parent = el.getparent()
    if parent is None:
        return
    idx = list(parent).index(el) + 1
    for offset, child in enumerate(_parse_children(str(p.get("html", p.get("value", ""))))):
        parent.insert(idx + offset, child)


def _op_remove(el, _p: dict) -> None:
    parent = el.getparent()
    if parent is not None:
        parent.remove(el)


_DISPATCH: dict[str, Callable] = {
    "setText": _op_set_text,
    "setHtml": _op_set_html,
    "setAttr": _op_set_attr,
    "removeAttr": _op_remove_attr,
    "addClass": _op_add_class,
    "removeClass": _op_remove_class,
    "appendInside": _op_append_inside,
    "prependInside": _op_prepend_inside,
    "insertBefore": _op_insert_before,
    "insertAfter": _op_insert_after,
    "remove": _op_remove,
}


def _apply_patches(html: str, patches: list[dict]) -> str:
    if not patches:
        return html
    root = _parse_fragment(html)
    for p in patches:
        op = p.get("op")
        handler = _DISPATCH.get(op)
        if not handler:
            continue
        selector = p.get("selector", "")
        for el in _select(root, selector):
            handler(el, p)
    return _serialise_fragment(root)


def _merge_nav(base: dict[str, str], overrides: dict[str, Any]) -> dict[str, str]:
    merged = dict(base)
    for key, val in (overrides or {}).items():
        full_key = key if key.startswith("on:") else f"on:{key}"
        if isinstance(val, dict) and "next_scene" in val:
            merged[full_key] = val["next_scene"]
        elif isinstance(val, str):
            merged[full_key] = val
    return merged


# --- Disk loaders --------------------------------------------------------

def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _manifest_path(versions_dir: Path, version_id: str) -> Path | None:
    for ext in (".yaml", ".yml"):
        p = versions_dir / f"{version_id}{ext}"
        if p.exists():
            return p
    return None


def discover_versions(scene_dir: Path) -> list[str]:
    """List version ids present on disk (one YAML manifest per version)."""
    versions_dir = scene_dir / "versions"
    if not versions_dir.exists():
        return []
    ids = {
        entry.stem
        for entry in versions_dir.iterdir()
        if entry.is_file() and entry.suffix in (".yaml", ".yml")
    }
    return sorted(ids)


def _base_spec(
    base_html: str, base_css: str, base_js: str, base_nav: dict[str, str]
) -> VersionSpec:
    return VersionSpec(
        id="base",
        html=base_html,
        css=base_css,
        js=base_js,
        nav_overrides=dict(base_nav),
        mode="base",
    )


def resolve_version(
    scene_dir: Path,
    version_id: str,
    base_html: str,
    base_css: str,
    base_js: str,
    base_nav: dict[str, str],
) -> VersionSpec:
    """Compute final html/css/js/nav for a scene at the requested version.

    ``version_id == "base"`` returns the unmodified base. Unknown versions
    silently fall back to base.
    """
    if version_id == "base":
        return _base_spec(base_html, base_css, base_js, base_nav)

    versions_dir = scene_dir / "versions"
    manifest_path = _manifest_path(versions_dir, version_id)
    if manifest_path is None:
        return _base_spec(base_html, base_css, base_js, base_nav)

    manifest = _load_yaml(manifest_path)

    html = manifest.get("html") or base_html
    css = manifest.get("css") or base_css
    js = manifest.get("js") or base_js

    if patches := manifest.get("patches") or []:
        html = _apply_patches(html, patches)

    if extra_css := manifest.get("css_append"):
        css = f"{css}\n\n/* {version_id} */\n{extra_css}"

    if extra_js := manifest.get("js_append"):
        js = f"{js}\n\n// {version_id}\n{extra_js}"

    nav = _merge_nav(base_nav, manifest.get("nav_overrides") or {})

    return VersionSpec(
        id=manifest.get("id", version_id),
        html=html,
        css=css,
        js=js,
        nav_overrides=nav,
        description=manifest.get("description"),
        mode="manifest",
    )
