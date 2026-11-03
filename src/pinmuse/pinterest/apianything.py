"""Bridge to api-anything (https://github.com/goodnight000/api-anything).

api-anything learns a website's own requests and shares them in a catalog. Its `pinterest` site
already exposes `searchSuggestions`; anything else (pin search, boards) can be learned with
`api-anything learn`. pinmuse calls it through its CLI so no extra code is needed on your side.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from ..models import Pin
from .web import best_image, parse_pin


def _cmd() -> list[str] | None:
    if shutil.which("api-anything"):
        return ["api-anything"]
    if shutil.which("npx"):
        return ["npx", "-y", "api-anything"]
    return None


def available() -> bool:
    return _cmd() is not None


def call(site: str, op: str, **args: Any) -> Any:
    base = _cmd()
    if not base:
        raise RuntimeError("api-anything not found: install Node 22+ and run `npm i -g api-anything`.")
    argv = base + ["call", site, op] + [f"{k}={v}" for k, v in args.items()]
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    out = proc.stdout.strip() or proc.stderr.strip()
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        raise RuntimeError(f"api-anything returned non-JSON output: {out[:400]}") from None
    if proc.returncode != 0 or (isinstance(payload, dict) and payload.get("ok") is False):
        raise RuntimeError(f"api-anything {site}.{op} failed: {json.dumps(payload)[:600]}")
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def suggestions(query: str) -> list[str]:
    data = call("pinterest", "searchSuggestions", q=query)
    return [d.get("query") or d.get("label") for d in data if isinstance(d, dict) and (d.get("query") or d.get("label"))]


def search(query: str, limit: int = 30, op: str = "searchPins") -> list[Pin]:
    """Uses a learned `pinterest.searchPins` op if your install or the catalog has one.

    If not, learn it once:  api-anything learn https://www.pinterest.com/search/pins/?q=ceramics
    """
    data = call("pinterest", op, q=query)
    pins: list[Pin] = []
    for d in data if isinstance(data, list) else []:
        p = parse_pin(d, source="api-anything")
        if not p and isinstance(d, dict):
            url, w, h = best_image(d.get("images"))
            url = url or d.get("image") or d.get("imageUrl") or ""
            if url:
                p = Pin(id=str(d.get("id", len(pins))), image_url=url, width=w, height=h,
                        title=d.get("title", ""), description=d.get("description", ""),
                        source="api-anything")
        if p:
            pins.append(p)
    return pins[:limit]
