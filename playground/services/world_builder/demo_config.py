"""Load and resolve demo.yaml for demo scenes."""

from __future__ import annotations

import copy
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from playground.config import get_settings

settings = get_settings()

DEMO_CUE_KINDS: frozenset[str] = frozenset(
    {"set", "show", "hide", "move", "zoom", "fade", "pause"}
)


class DemoCueKind(StrEnum):
    SET = "set"
    SHOW = "show"
    HIDE = "hide"
    MOVE = "move"
    ZOOM = "zoom"
    FADE = "fade"
    PAUSE = "pause"


def _scene_dir(world_id: str, scene_id: str) -> Path:
    return settings.worlds_content_dir / world_id / "scenes" / scene_id


def demo_yaml_path(world_id: str, scene_id: str) -> Path:
    return _scene_dir(world_id, scene_id) / "demo.yaml"


def load_demo_yaml(world_id: str, scene_id: str) -> dict[str, Any] | None:
    """Return parsed demo.yaml or None if this scene is not a demo scene."""
    path = demo_yaml_path(world_id, scene_id)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"demo.yaml must be a mapping: {path}")
    validate_demo_config(data, source=str(path))
    return data


def validate_demo_config(config: dict[str, Any], *, source: str = "demo.yaml") -> None:
    """Validate demo config; raise ValueError on unknown cue kinds or bad timeline."""
    timeline = config.get("timeline") or []
    if not isinstance(timeline, list):
        raise ValueError(f"{source}: timeline must be a list")
    for i, cue in enumerate(timeline):
        if not isinstance(cue, dict):
            raise ValueError(f"{source}: timeline[{i}] must be a mapping")
        kind = cue.get("kind")
        if kind is None:
            raise ValueError(f"{source}: timeline[{i}] missing kind")
        if kind not in DEMO_CUE_KINDS:
            raise ValueError(f"{source}: unknown cue kind {kind!r}")


def _deep_merge_layers(
    base_layers: list[dict[str, Any]],
    overrides: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {layer["id"]: copy.deepcopy(layer) for layer in base_layers if "id" in layer}
    for layer_id, patch in overrides.items():
        if layer_id not in by_id:
            continue
        if isinstance(patch, dict):
            merged = copy.deepcopy(by_id[layer_id])
            for key, val in patch.items():
                if key == "initial" and isinstance(val, dict):
                    merged.setdefault("initial", {})
                    merged["initial"].update(val)
                else:
                    merged[key] = val
            by_id[layer_id] = merged
    return list(by_id.values())


def resolve_demo_config_for_device(
    config: dict[str, Any],
    *,
    is_mobile: bool,
    mobile_max_width: int = 768,
) -> dict[str, Any]:
    """Apply mobile overrides and filter timeline cues by device."""
    resolved = copy.deepcopy(config)
    mobile = config.get("mobile") or {}
    if is_mobile and mobile:
        if "length" in mobile:
            resolved["length"] = mobile["length"]
        for key in ("scrub", "pin", "default_ease", "background", "progress_bar"):
            if key in mobile:
                resolved[key] = mobile[key]
        if "layers" in mobile and isinstance(mobile["layers"], dict):
            resolved["layers"] = _deep_merge_layers(
                resolved.get("layers") or [],
                mobile["layers"],
            )
        if "timeline" in mobile:
            resolved["timeline"] = copy.deepcopy(mobile["timeline"])
    resolved["_device"] = "mobile" if is_mobile else "desktop"
    resolved["_mobile_max_width"] = mobile.get("max_width", mobile_max_width)
    resolved["timeline"] = filter_timeline_by_device(
        resolved.get("timeline") or [],
        device="mobile" if is_mobile else "desktop",
    )
    return resolved


def filter_timeline_by_device(
    timeline: list[dict[str, Any]],
    *,
    device: str,
) -> list[dict[str, Any]]:
    """Keep cues where device is all or matches the active device class."""
    out: list[dict[str, Any]] = []
    for cue in timeline:
        cue_device = cue.get("device", "all")
        if cue_device in ("all", device):
            out.append(cue)
    return out


def scene_assets_url_prefix(world_id: str, scene_id: str) -> str:
    return f"/worlds/{world_id}/scenes/{scene_id}/assets"
