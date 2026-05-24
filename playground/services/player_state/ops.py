"""Atomic state mutation operations."""

from copy import deepcopy
from typing import Any


def apply_op(current: Any, op: str, value: Any) -> Any:
    if op == "set":
        return value
    if op == "append":
        if current is None:
            current = []
        if not isinstance(current, list):
            raise ValueError("append requires list value")
        new = list(current)
        new.append(value)
        return new
    if op == "remove":
        if not isinstance(current, list):
            raise ValueError("remove requires list value")
        new = list(current)
        if value in new:
            new.remove(value)
        return new
    if op == "inc":
        base = current if isinstance(current, (int, float)) else 0
        delta = value if isinstance(value, (int, float)) else 1
        return base + delta
    if op == "merge":
        if not isinstance(value, dict):
            raise ValueError("merge requires dict value")
        base = deepcopy(current) if isinstance(current, dict) else {}
        base.update(value)
        return base
    raise ValueError(f"unknown op: {op}")
