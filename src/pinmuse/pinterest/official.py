"""Official Pinterest API v5 — use your own boards and pins with an access token.

Create an app at https://developers.pinterest.com/apps/ and set PINTEREST_ACCESS_TOKEN
(scopes: boards:read, pins:read). This is the most stable, ToS-friendly source for *your* boards.
"""

from __future__ import annotations

from typing import Any

from .. import http
from ..config import setting
from ..models import Pin

API = "https://api.pinterest.com/v5"


def _token() -> str:
    t = setting("pinterest_access_token")
    if not t:
        raise RuntimeError("Set PINTEREST_ACCESS_TOKEN to use the official Pinterest API backend.")
    return t


def available() -> bool:
    return bool(setting("pinterest_access_token"))


def _get(path: str, **params: Any) -> dict:
    return http.get_json(API + path, params={k: v for k, v in params.items() if v is not None},
                         headers={"Authorization": f"Bearer {_token()}"})


def _paged(path: str, limit: int, **params: Any) -> list[dict]:
    out: list[dict] = []
    bookmark = None
    while len(out) < limit:
        resp = _get(path, page_size=min(100, limit), bookmark=bookmark, **params)
        out += resp.get("items", [])
        bookmark = resp.get("bookmark")
        if not bookmark:
            break
    return out[:limit]


def _to_pin(item: dict) -> Pin | None:
    media = item.get("media") or {}
    images = media.get("images") or {}
    best = None
    for key in ("originals", "1200x", "600x", "400x300", "150x150"):
        if key in images:
            best = images[key]
            break
    if not best and media.get("items"):  # carousel pins
        imgs = (media["items"][0] or {}).get("images") or {}
        best = next(iter(imgs.values()), None)
    if not best:
        return None
    return Pin(
        id=str(item.get("id")),
        image_url=best.get("url", ""),
        width=int(best.get("width") or 0),
        height=int(best.get("height") or 0),
        title=item.get("title") or "",
        description=item.get("description") or item.get("alt_text") or "",
        link=item.get("link") or "",
        url=f"https://www.pinterest.com/pin/{item.get('id')}/",
        dominant_color=item.get("dominant_color") or "",
        board=item.get("board_id") or "",
        source="official",
    )


def boards(limit: int = 100) -> list[dict]:
    return [{"id": b["id"], "name": b.get("name"), "description": b.get("description"),
             "pin_count": b.get("pin_count")} for b in _paged("/boards", limit)]


def board_pins(board_id: str, limit: int = 50) -> list[Pin]:
    return [p for p in (_to_pin(i) for i in _paged(f"/boards/{board_id}/pins", limit)) if p]


def search_my_pins(query: str, limit: int = 50) -> list[Pin]:
    return [p for p in (_to_pin(i) for i in _paged("/search/pins", limit, query=query)) if p]


def pin(pin_id: str) -> Pin | None:
    return _to_pin(_get(f"/pins/{pin_id}"))


def create_pin(board_id: str, image_url: str, title: str, description: str = "", link: str = "") -> dict:
    """Publish a finished design back to the user's board (only when they ask you to)."""
    body = {"board_id": board_id, "title": title[:100], "description": description[:500],
            "media_source": {"source_type": "image_url", "url": image_url}}
    if link:
        body["link"] = link
    return http.post_json(API + "/pins", body, headers={"Authorization": f"Bearer {_token()}"})
