"""Pinterest explorer: one `explore()` call, several interchangeable backends.

Backends (tried in this order with `--source auto`):
  web           signed-out pinterest.com JSON resources (no key)
  api-anything  goodnight000/api-anything learned ops (shared catalog)
  browser       headless Chromium via Playwright
  official      Pinterest API v5 with PINTEREST_ACCESS_TOKEN (your own boards/pins)
  local:<dir>   a folder of images
"""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import http
from ..config import CACHE_DIR
from ..models import Pin
from . import apianything, browser, local, official, web

SOURCES = ["web", "api-anything", "browser", "official", "local"]
_TTL = 6 * 3600


def _cache_key(*parts: object) -> Path:
    h = hashlib.sha1(json.dumps(parts, default=str).encode()).hexdigest()[:16]
    return CACHE_DIR / "search" / f"{h}.json"


def explore(target: str, limit: int = 30, source: str = "auto", use_cache: bool = True) -> tuple[list[Pin], list[str]]:
    """Return (pins, log). `target` is a search phrase, a pin URL, or a board URL."""
    log: list[str] = []
    if source.startswith("local:") or (source == "auto" and Path(target).expanduser().is_dir()):
        folder = source.split(":", 1)[1] if source.startswith("local:") else target
        pins = local.search(folder, limit)
        log.append(f"local: {len(pins)} images from {folder}")
        return pins, log

    key = _cache_key(target, limit, source)
    if use_cache and key.exists() and time.time() - key.stat().st_mtime < _TTL:
        pins = [Pin.from_dict(d) for d in json.loads(key.read_text())]
        log.append(f"cache: {len(pins)} pins")
        return pins, log

    order = SOURCES[:-1] if source == "auto" else [source]
    pins: list[Pin] = []
    for name in order:
        try:
            if name == "web":
                pins = list(web.iter_any(target, limit))
            elif name == "api-anything":
                if not apianything.available():
                    log.append("api-anything: not installed, skipped")
                    continue
                pins = apianything.search(target, limit)
            elif name == "browser":
                if not browser.available():
                    log.append("browser: playwright not installed, skipped")
                    continue
                pins = browser.search(target, limit)
            elif name == "official":
                if not official.available():
                    log.append("official: no PINTEREST_ACCESS_TOKEN, skipped")
                    continue
                pins = official.search_my_pins(target, limit)
            else:
                raise ValueError(f"unknown source {name!r}; choose from {SOURCES}")
            log.append(f"{name}: {len(pins)} pins")
            if pins:
                break
        except Exception as e:  # noqa: BLE001 — fall through to the next backend
            log.append(f"{name}: failed ({type(e).__name__}: {str(e)[:160]})")
    if pins:
        key.parent.mkdir(parents=True, exist_ok=True)
        key.write_text(json.dumps([p.to_dict() for p in pins]))
    return pins, log


def suggest(query: str) -> list[str]:
    """Expand an idea into Pinterest's own related searches (the 'aesthetic rabbit hole')."""
    try:
        return web.suggestions(query)
    except Exception:  # noqa: BLE001
        if apianything.available():
            return apianything.suggestions(query)
        raise


def download(pins: list[Pin], dest: Path | None = None, workers: int = 6) -> list[Pin]:
    """Cache pin images locally (needed for palette analysis + reference-guided generation)."""
    dest = dest or CACHE_DIR / "images"
    dest.mkdir(parents=True, exist_ok=True)

    def fetch(p: Pin) -> Pin:
        if p.local_path and Path(p.local_path).exists():
            return p
        ext = Path(p.image_url.split("?")[0]).suffix or ".jpg"
        f = dest / (hashlib.sha1(p.image_url.encode()).hexdigest()[:16] + ext)
        if not f.exists():
            try:
                f.write_bytes(http.request("GET", p.image_url, headers={"Referer": "https://www.pinterest.com/"},
                                           timeout=40))
            except Exception:  # noqa: BLE001
                return p
        p.local_path = str(f)
        return p

    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fetch, pins))
