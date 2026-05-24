"""Generic server-side pagination for admin list views."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any
from urllib.parse import urlencode

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


@dataclass
class Pagination:
    page: int
    page_size: int
    total: int
    total_pages: int
    offset: int
    has_prev: bool
    has_next: bool
    prev_url: str | None
    next_url: str | None

    @classmethod
    def build(
        cls,
        *,
        total: int,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        base_path: str,
        query_params: dict[str, Any] | None = None,
    ) -> Pagination:
        page_size = max(1, min(page_size, MAX_PAGE_SIZE))
        total_pages = max(1, ceil(total / page_size)) if total else 1
        page = max(1, min(page, total_pages))
        offset = (page - 1) * page_size
        has_prev = page > 1
        has_next = page < total_pages
        qp = _stringify_params(query_params)
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            offset=offset,
            has_prev=has_prev,
            has_next=has_next,
            prev_url=_page_url(base_path, qp, page - 1, page_size) if has_prev else None,
            next_url=_page_url(base_path, qp, page + 1, page_size) if has_next else None,
        )


def _stringify_params(params: dict[str, Any] | None) -> dict[str, str]:
    if not params:
        return {}
    out: dict[str, str] = {}
    for key, val in params.items():
        if val is None or val == "":
            continue
        out[key] = str(val)
    return out


def _page_url(
    base_path: str,
    query_params: dict[str, str],
    page: int,
    page_size: int,
) -> str:
    params = dict(query_params)
    params["page"] = str(page)
    params["page_size"] = str(page_size)
    return f"{base_path}?{urlencode(params)}"
