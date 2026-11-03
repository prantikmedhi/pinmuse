"""Headless-browser fallback (Playwright). Scrolls a real Pinterest page and reads the grid.

pip install playwright && playwright install chromium
"""

from __future__ import annotations

from urllib.parse import quote

from ..models import Pin
from .web import upgrade_pinimg


def available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def search(query_or_url: str, limit: int = 30, scrolls: int = 8) -> list[Pin]:
    from playwright.sync_api import sync_playwright

    url = query_or_url if query_or_url.startswith("http") else (
        f"https://www.pinterest.com/search/pins/?q={quote(query_or_url)}")
    pins: list[Pin] = []
    seen: set[str] = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1800})
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2500)
        for _ in range(scrolls):
            rows = page.eval_on_selector_all(
                "a[href*='/pin/'] img[src*='pinimg.com']",
                """els => els.map(img => ({src: img.currentSrc || img.src, alt: img.alt || '',
                     href: img.closest('a').href}))""",
            )
            for r in rows:
                href = r["href"]
                pid = href.rstrip("/").split("/pin/")[-1].split("/")[0]
                if pid in seen:
                    continue
                seen.add(pid)
                pins.append(Pin(id=pid, image_url=upgrade_pinimg(r["src"]), description=r["alt"],
                                url=href, source="browser"))
            if len(pins) >= limit:
                break
            page.mouse.wheel(0, 2200)
            page.wait_for_timeout(1200)
        browser.close()
    return pins[:limit]
