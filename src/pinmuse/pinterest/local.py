"""Use a folder of images (downloaded boards, exports, your own references) as the inspiration source."""

from __future__ import annotations

from pathlib import Path

from ..models import Pin

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def search(folder: str, limit: int = 60) -> list[Pin]:
    root = Path(folder).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"not a folder: {root}")
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in EXTS)[:limit]
    pins = []
    for f in files:
        title = f.stem.replace("-", " ").replace("_", " ")
        pins.append(Pin(id=f.stem, image_url=f.resolve().as_uri(), title=title,
                        local_path=str(f.resolve()), source="local"))
    return pins
