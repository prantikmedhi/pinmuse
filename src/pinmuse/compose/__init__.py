"""Compose finished, post-ready designs from generated (or any) images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from . import effects as fx
from .layouts import TEMPLATES, Design


def _logo(img: Image.Image, logo: str) -> Image.Image:
    if not logo or not Path(logo).exists():
        return img
    lg = Image.open(logo).convert("RGBA")
    s = int(img.width * .12)
    lg.thumbnail((s, s))
    img = img.convert("RGBA")
    m = int(img.width * .05)
    img.alpha_composite(lg, (img.width - lg.width - m, img.height - lg.height - m - int(img.width * .05)))
    return img.convert("RGB")


def render(ds: Design, out: Path) -> list[Path]:
    if ds.template not in TEMPLATES:
        raise KeyError(f"unknown template {ds.template!r}. Options: {', '.join(TEMPLATES)}")
    result = TEMPLATES[ds.template](ds)
    frames = result if isinstance(result, list) else [result]
    out.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, im in enumerate(frames):
        if ds.template != "carousel" or i == 0:
            im = fx.apply(im, ds.effects, ds.palette)
        im = _logo(im, ds.logo)
        p = out if len(frames) == 1 else out.with_name(f"{out.stem}-{i + 1:02d}{out.suffix}")
        im.convert("RGB").save(p, quality=95)
        paths.append(p)
    return paths


__all__ = ["Design", "TEMPLATES", "render"]
