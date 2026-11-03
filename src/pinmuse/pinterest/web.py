"""Signed-out Pinterest via the same JSON resources pinterest.com's own frontend calls.

No account, no API key. Public data only, fetched at human volume (throttled + cached).
If Pinterest changes these resources, the `browser` and `api-anything` backends are fallbacks.
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterator
from urllib.parse import quote, urlparse

from .. import http
from ..models import Pin

BASE = "https://www.pinterest.com"

_HEADERS = {
    "Accept": "application/json, text/javascript, */*, q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "X-Pinterest-AppState": "active",
    "Referer": BASE + "/",
}


def _resource(name: str, source_url: str, options: dict[str, Any], handler: str | None = None) -> dict:
    headers = dict(_HEADERS)
    headers["X-Pinterest-Source-Url"] = source_url
    if handler:
        headers["X-Pinterest-PWS-Handler"] = handler
    data = json.dumps({"options": options, "context": {}}, separators=(",", ":"))
    return http.get_json(
        f"{BASE}/resource/{name}/get/",
        params={"source_url": source_url, "data": data},
        headers=headers,
        throttle=True,
    )


def best_image(images: dict[str, Any] | None) -> tuple[str, int, int]:
    """Pick the largest image variant Pinterest returned."""
    if not images:
        return "", 0, 0
    for key in ("orig", "originals", "1200x", "736x", "474x", "236x", "170x"):
        v = images.get(key)
        if isinstance(v, dict) and v.get("url"):
            return v["url"], int(v.get("width") or 0), int(v.get("height") or 0)
    for v in images.values():
        if isinstance(v, dict) and v.get("url"):
            return v["url"], int(v.get("width") or 0), int(v.get("height") or 0)
    return "", 0, 0


def upgrade_pinimg(url: str, size: str = "736x") -> str:
    """i.pinimg.com/236x/ab/cd/… → a larger rendition (originals or 736x)."""
    return re.sub(r"i\.pinimg\.com/(\d+x(\d+)?|originals)/", f"i.pinimg.com/{size}/", url)


def parse_pin(obj: dict[str, Any], source: str = "web") -> Pin | None:
    if not isinstance(obj, dict) or obj.get("type") not in (None, "pin"):
        return None
    if obj.get("is_promoted") or obj.get("ad_match_reason"):
        return None  # skip ads
    url, w, h = best_image(obj.get("images"))
    if not url and obj.get("image_large_url"):
        url = obj["image_large_url"]
    if not url:
        return None
    stats = (obj.get("aggregated_pin_data") or {}).get("aggregated_stats") or {}
    rich = obj.get("rich_summary") or {}
    pid = str(obj.get("id") or "")
    return Pin(
        id=pid,
        image_url=url,
        title=(obj.get("grid_title") or obj.get("title") or rich.get("display_name") or "").strip(),
        description=(obj.get("description") or obj.get("closeup_unified_description") or "").strip(),
        link=obj.get("link") or "",
        url=f"{BASE}/pin/{pid}/" if pid else "",
        width=w,
        height=h,
        dominant_color=obj.get("dominant_color") or "",
        saves=int(stats.get("saves") or obj.get("repin_count") or 0),
        board=((obj.get("board") or {}).get("name") or ""),
        pinner=((obj.get("pinner") or {}).get("username") or ""),
        source=source,
        extra={k: obj[k] for k in ("auto_alt_text", "seo_alt_text", "category") if obj.get(k)},
    )


def _results(resp: dict) -> tuple[list[dict], str | None]:
    rr = resp.get("resource_response") or {}
    data = rr.get("data")
    bookmark = rr.get("bookmark")
    if isinstance(data, dict):
        items = data.get("results") or data.get("items") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []
    if bookmark in ("-end-", ""):
        bookmark = None
    return items, bookmark


def search(query: str, limit: int = 30, scope: str = "pins") -> list[Pin]:
    """Search public pins. Paginates with bookmarks until `limit` pins are collected."""
    pins: list[Pin] = []
    seen: set[str] = set()
    bookmark: str | None = None
    source_url = f"/search/{scope}/?q={quote(query)}&rs=typed"
    for _ in range(10):
        opts: dict[str, Any] = {
            "query": query,
            "scope": scope,
            "page_size": min(50, max(10, limit)),
            "rs": "typed",
            "redux_normalize_feed": True,
        }
        if bookmark:
            opts["bookmarks"] = [bookmark]
        resp = _resource("BaseSearchResource", source_url, opts, "www/search/[scope].js")
        items, bookmark = _results(resp)
        for it in items:
            p = parse_pin(it)
            if p and p.id not in seen:
                seen.add(p.id)
                pins.append(p)
        if len(pins) >= limit or not bookmark or not items:
            break
    return pins[:limit]


def suggestions(query: str, count: int = 8) -> list[str]:
    """Pinterest's own typeahead — great for expanding a vague idea into searchable aesthetics."""
    resp = _resource(
        "AdvancedTypeaheadResource",
        f"/search/pins/?q={quote(query)}",
        {"pin_scope": "pins", "count": count, "term": query, "autocomplete_request_surface": 0},
    )
    items, _ = _results(resp)
    out = []
    for it in items:
        q = it.get("query") or it.get("label")
        if q and it.get("type", "query") != "user" and q not in out:
            out.append(q)
    return out


def pin(pin_id: str) -> Pin | None:
    resp = _resource(
        "PinResource",
        f"/pin/{pin_id}/",
        {"id": pin_id, "field_set_key": "detailed"},
    )
    data = (resp.get("resource_response") or {}).get("data")
    return parse_pin(data) if data else None


def related(pin_id: str, limit: int = 25) -> list[Pin]:
    """'More like this' for a pin — the core of a Pinterest rabbit hole."""
    resp = _resource(
        "RelatedModulesResource",
        f"/pin/{pin_id}/",
        {"pin_id": pin_id, "context_pin_ids": [], "search_query": "", "source": "deep_linking",
         "top_level_source": "deep_linking", "page_size": limit},
    )
    items, _ = _results(resp)
    pins = [p for p in (parse_pin(i) for i in items) if p]
    return pins[:limit]


def board(board_url: str, limit: int = 50) -> list[Pin]:
    """Pins from a public board, given its URL (https://pinterest.com/<user>/<board>/)."""
    path = urlparse(board_url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("board URL must look like https://www.pinterest.com/<user>/<board>/")
    user, slug = parts[0], parts[1]
    src = f"/{user}/{slug}/"
    meta = _resource("BoardResource", src, {"username": user, "slug": slug, "field_set_key": "detailed"})
    board_id = ((meta.get("resource_response") or {}).get("data") or {}).get("id")
    if not board_id:
        return _scrape_html(BASE + src, limit)
    pins: list[Pin] = []
    bookmark = None
    for _ in range(10):
        opts: dict[str, Any] = {"board_id": board_id, "board_url": src, "page_size": 50,
                                "field_set_key": "react_grid_pin", "redux_normalize_feed": True}
        if bookmark:
            opts["bookmarks"] = [bookmark]
        items, bookmark = _results(_resource("BoardFeedResource", src, opts))
        pins += [p for p in (parse_pin(i) for i in items) if p]
        if len(pins) >= limit or not bookmark:
            break
    return pins[:limit]


def user_pins(username: str, limit: int = 50) -> list[Pin]:
    src = f"/{username}/_created/"
    items, _ = _results(_resource("UserActivityPinsResource", src,
                                  {"username": username, "page_size": limit, "field_set_key": "grid_item"}))
    return [p for p in (parse_pin(i) for i in items) if p][:limit]


_PINIMG = re.compile(r"https://i\.pinimg\.com/[^\s\"'\\]+?\.(?:jpg|jpeg|png|webp)")


def _scrape_html(url: str, limit: int) -> list[Pin]:
    """Last-ditch: pull pinimg URLs out of a page's HTML/embedded JSON."""
    html = http.request("GET", url, headers={"Accept": "text/html"}, throttle=True).decode("utf-8", "replace")
    pins: list[Pin] = []
    seen: set[str] = set()
    for m in _PINIMG.finditer(html):
        u = upgrade_pinimg(m.group(0))
        key = u.rsplit("/", 1)[-1]
        if key in seen or "/75x75" in u or "/30x30" in u:
            continue
        seen.add(key)
        pins.append(Pin(id=key.split(".")[0], image_url=u, url=url, source="html"))
        if len(pins) >= limit:
            break
    return pins


def iter_any(target: str, limit: int) -> Iterator[Pin]:
    """Dispatch on what the user gave us: a search phrase, a pin URL, or a board URL."""
    if target.startswith("http"):
        m = re.search(r"/pin/(\d+)", target)
        if m:
            root = pin(m.group(1))
            if root:
                yield root
            yield from related(m.group(1), limit - 1)
            return
        yield from board(target, limit)
        return
    yield from search(target, limit)
