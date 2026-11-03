"""No model, no key: palette-driven generative art with Pillow + numpy.

Always available, deterministic per prompt. Good for backgrounds, quote cards, palette posts,
offline demos — and the fallback when nothing else is configured.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .. import aesthetics
from .base import GenRequest, Provider


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _lum(c) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def mesh(w: int, h: int, pal: list, rng: np.random.Generator, blobs: int = 7) -> Image.Image:
    """Soft gradient mesh — the 'blurry aura' look."""
    base = Image.new("RGB", (w // 4, h // 4), pal[0])
    d = ImageDraw.Draw(base)
    for i in range(blobs):
        c = pal[(i % (len(pal) - 1)) + 1]
        r = int(rng.uniform(.25, .6) * max(w, h) / 4)
        x, y = rng.uniform(0, w / 4), rng.uniform(0, h / 4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    return base.filter(ImageFilter.GaussianBlur(max(w, h) / 4 * .12)).resize((w, h), Image.BICUBIC)


def sunset(w: int, h: int, pal: list, rng: np.random.Generator) -> Image.Image:
    """Retro sun + horizon grid (vaporwave / synthwave / y2k)."""
    top, mid, low = np.array(pal[0], float), np.array(pal[1], float), np.array(pal[-1], float)
    t = np.linspace(0, 1, h)[:, None, None]
    sky = np.where(t < .62, top + (mid - top) * (t / .62), mid + (low - mid) * ((t - .62) / .38))
    img = Image.fromarray(np.broadcast_to(sky, (h, w, 3)).astype(np.uint8))
    d = ImageDraw.Draw(img)
    cx, cy, r = w / 2, h * .5, w * .28
    sun = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sun).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    for i in range(7):  # sun slices
        y = cy + r * (.15 + i * .12)
        ImageDraw.Draw(sun).rectangle([0, y, w, y + 4 + i * 2.2], fill=0)
    img.paste(Image.new("RGB", (w, h), pal[2 % len(pal)]), (0, 0), sun)
    hz = int(h * .62)
    d.rectangle([0, hz, w, h], fill=tuple(int(v * .35) for v in pal[0]))
    line = pal[1 if _lum(pal[1]) > 90 else 3 % len(pal)]
    for i in range(1, 14):
        y = hz + (h - hz) * (i / 13) ** 1.9
        d.line([0, y, w, y], fill=line, width=2)
    for i in range(-14, 15):
        d.line([cx + i * w * .03, hz, cx + i * w * .25, h], fill=line, width=2)
    return img


def arches(w: int, h: int, pal: list, rng: np.random.Generator) -> Image.Image:
    """Layered arches and a sun disc — minimal / boho / luxe still-life feel."""
    img = Image.new("RGB", (w, h), pal[0])
    d = ImageDraw.Draw(img)
    n = 4
    for i in range(n):
        aw = w * (.78 - i * .15)
        x0 = (w - aw) / 2
        y0 = h * (.36 + i * .08)
        c = pal[(i + 1) % len(pal)]
        d.rounded_rectangle([x0, y0, x0 + aw, h * 1.1], radius=int(aw / 2), fill=c)
    r = w * .1
    sx, sy = w * rng.uniform(.66, .76), h * rng.uniform(.33, .37)
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=pal[-1] if _lum(pal[-1]) < 200 else pal[2 % len(pal)])
    d.rectangle([0, h * .86, w, h], fill=tuple(max(0, int(v * .88)) for v in pal[1]))
    return img


def swiss(w: int, h: int, pal: list, rng: np.random.Generator) -> Image.Image:
    """Bold geometric composition — brutalist / swiss / pop."""
    img = Image.new("RGB", (w, h), pal[0])
    d = ImageDraw.Draw(img)
    u = w / 6
    accent = max(pal, key=lambda c: (max(c) - min(c)))
    dark = min(pal, key=_lum)
    d.ellipse([u * 1, h * .18, u * 5.4, h * .18 + u * 4.4], fill=accent)
    d.rectangle([0, h * .55, u * 3, h], fill=dark)
    for i in range(9):
        d.rectangle([u * 3.3 + i * u * .3, h * .62, u * 3.42 + i * u * .3, h * .95], fill=dark)
    d.polygon([(u * 4, h * .1), (w, h * .1), (w, h * .4)], fill=pal[2 % len(pal)])
    return img


def bokeh(w: int, h: int, pal: list, rng: np.random.Generator) -> Image.Image:
    """Night bokeh + light streaks — neon / gothic / moody."""
    dark = min(pal, key=_lum)
    img = mesh(w, h, [dark] + [tuple(int(v * .45) for v in c) for c in pal[1:]], rng, 5)
    layer = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    bright = sorted(pal, key=lambda c: -(max(c) - min(c)))[:3]
    for _ in range(70):
        c = bright[int(rng.integers(0, len(bright)))]
        r = rng.uniform(.01, .06) * w
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * rng.uniform(.35, .9)) for v in c))
    layer = layer.filter(ImageFilter.GaussianBlur(w * .006))
    return Image.fromarray(np.clip(np.asarray(img, int) + np.asarray(layer, int), 0, 255).astype(np.uint8))


def waves(w: int, h: int, pal: list, rng: np.random.Generator) -> Image.Image:
    """Stacked organic waves — pastel / coastal / cottage."""
    img = Image.new("RGB", (w, h), pal[0])
    d = ImageDraw.Draw(img)
    bands = len(pal) + 1
    for i in range(bands):
        c = pal[(i + 1) % len(pal)]
        base = h * (.28 + i * .62 / bands)
        amp, freq, ph = h * rng.uniform(.02, .05), rng.uniform(1.2, 2.6), rng.uniform(0, 6.28)
        pts = [(x, base + amp * math.sin(freq * 2 * math.pi * x / w + ph)) for x in range(0, w + 8, 8)]
        d.polygon(pts + [(w, h), (0, h)], fill=c)
    r = w * .13
    d.ellipse([w * .66 - r, h * .14 - r, w * .66 + r, h * .14 + r], fill=pal[-2 % len(pal)])
    return img


STYLE_FOR = {
    "vaporwave": "sunset", "y2k": "mesh", "cyberpunk-neon": "bokeh", "gothic-romance": "bokeh",
    "moody-film": "mesh", "minimal-luxe": "arches", "earthy-boho": "arches", "old-money": "arches",
    "brutalist": "swiss", "pastel-dream": "waves", "coastal-summer": "waves", "cottagecore": "waves",
    "dark-academia": "mesh", "clean-girl": "mesh",
}
STYLES = {"mesh": mesh, "sunset": sunset, "arches": arches, "swiss": swiss, "bokeh": bokeh, "waves": waves}


def grain(img: Image.Image, amount: float = 0.06, seed: int = 0) -> Image.Image:
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.float32)
    noise = rng.normal(0, 255 * amount, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + noise, 0, 255).astype(np.uint8))


class ProceduralProvider(Provider):
    name, kind = "procedural", "builtin"
    setup = "always on — no model or key (style via PINMUSE_PROCEDURAL_STYLE=mesh|sunset|arches|swiss|bokeh|waves)"

    def available(self) -> bool:
        return True

    def generate(self, req: GenRequest, style: str | None = None) -> Path:
        from ..config import setting
        seed = req.seed if req.seed is not None else int(hashlib.sha1(req.prompt.encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        a = aesthetics.PRESETS.get(req.aesthetic)
        pal_hex = req.palette or (list(a.palette) if a else list(aesthetics.PRESETS[aesthetics.DEFAULT].palette))
        pal = [_rgb(c) for c in pal_hex] + [_rgb(pal_hex[0])] * max(0, 3 - len(pal_hex))
        style = style or setting("procedural_style") or STYLE_FOR.get(req.aesthetic, "mesh")
        img = STYLES[style](req.width, req.height, pal, rng)
        img = grain(img, 0.045, seed)
        req.out.parent.mkdir(parents=True, exist_ok=True)
        img.save(req.out)
        return req.out
