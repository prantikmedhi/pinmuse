"""Turn a pile of pins into a visual direction: palette, mood metrics, motifs, a named aesthetic."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from . import aesthetics
from .models import Moodboard, Pin

STOP = set("""a an and are as at be by for from has have i in is it its of on or our so that the this to was
were will with you your my me we us they them their how what when where who why not no yes all any more most
can just get got make made new best top ideas idea inspo inspiration aesthetic aesthetics pin pins pinterest
diy easy cute love like look looks one two 2024 2025 2026 amp via http https www com html jpg png pic photo
photos image images""".split())


def hex_of(rgb) -> str:
    return "#%02X%02X%02X" % tuple(int(c) for c in rgb[:3])


def rgb_of(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _load(p: Pin, size: int = 160) -> Image.Image | None:
    if not p.local_path or not Path(p.local_path).exists():
        return None
    try:
        im = Image.open(p.local_path)
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((size, size))
        return im
    except Exception:  # noqa: BLE001
        return None


def palette(images: list[Image.Image], k: int = 6) -> tuple[list[str], list[float]]:
    """Dominant colours across all images (median-cut on a stitched strip), most common first."""
    if not images:
        return [], []
    strip = Image.new("RGB", (160 * len(images), 160))
    for i, im in enumerate(images):
        strip.paste(im.resize((160, 160)), (160 * i, 0))
    q = strip.quantize(colors=k * 3, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[: k * 3 * 3]
    counts = sorted(q.getcolors(), reverse=True)
    picked: list[tuple[tuple[int, int, int], int]] = []
    for count, idx in counts:
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        # merge near-duplicates so the palette stays varied
        if all(sum((a - b) ** 2 for a, b in zip(rgb, other)) > 900 for other, _ in picked):
            picked.append((rgb, count))  # type: ignore[arg-type]
        if len(picked) == k:
            break
    total = sum(c for _, c in picked) or 1
    return [hex_of(c) for c, _ in picked], [round(n / total, 3) for _, n in picked]


def metrics(images: list[Image.Image]) -> dict[str, float]:
    if not images:
        return {"brightness": .5, "contrast": .5, "saturation": .3, "warmth": 0.0}
    arr = np.concatenate([np.asarray(im.resize((96, 96)), dtype=np.float32).reshape(-1, 3) for im in images]) / 255
    lum = arr @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    mx, mn = arr.max(1), arr.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    warmth = float(np.clip((arr[:, 0].mean() - arr[:, 2].mean()) * 4, -1, 1))
    return {"brightness": round(float(lum.mean()), 3), "contrast": round(float(min(1, lum.std() * 3.2)), 3),
            "saturation": round(float(sat.mean()), 3), "warmth": round(warmth, 3)}


def keywords(pins: list[Pin], n: int = 20) -> list[str]:
    words: Counter[str] = Counter()
    for p in pins:
        text = " ".join([p.text, " ".join(str(v) for v in p.extra.values())]).lower()
        toks = [t for t in re.findall(r"[a-z][a-z'-]{2,}", text) if t not in STOP]
        words.update(toks)
        words.update(f"{a} {b}" for a, b in zip(toks, toks[1:]))  # bigrams carry style ("old money")
    ranked = [w for w, c in words.most_common(n * 3) if c > 1 or len(pins) < 6]
    out: list[str] = []
    for w in ranked:
        if not any(w != o and w in o.split() for o in out):  # prefer bigram over its words
            out.append(w)
        if len(out) == n:
            break
    return out


def _color_dist(a: str, b: str) -> float:
    return float(np.sqrt(sum((x - y) ** 2 for x, y in zip(rgb_of(a), rgb_of(b)))) / 441.7)


def score_aesthetics(pal: list[str], m: dict[str, float], kws: list[str], query: str = "") -> dict[str, float]:
    text = " ".join(kws + [query.lower()])
    scores = {}
    for name, a in aesthetics.PRESETS.items():
        kw = sum(1 for k in a.keywords if k in text) / max(3, len(a.keywords) * .5)
        pd = np.mean([min(_color_dist(c, t) for t in a.palette) for c in pal]) if pal else .5
        t = a.target
        md = np.mean([abs(m["brightness"] - t["brightness"]), abs(m["saturation"] - t["saturation"]),
                      abs(m["warmth"] - t["warmth"]) / 2]) if t else .5
        scores[name] = round(float(0.45 * min(1, kw) + 0.30 * (1 - pd) + 0.25 * (1 - md)), 3)
    return dict(sorted(scores.items(), key=lambda kv: -kv[1]))


def describe(m: dict[str, float]) -> list[str]:
    d = []
    d.append("airy, high-key" if m["brightness"] > .68 else "moody, low-key" if m["brightness"] < .36 else "balanced exposure")
    d.append("muted / desaturated" if m["saturation"] < .22 else "vivid, saturated" if m["saturation"] > .55 else "natural colour")
    d.append("warm tones" if m["warmth"] > .2 else "cool tones" if m["warmth"] < -.15 else "neutral white balance")
    d.append("high contrast" if m["contrast"] > .62 else "soft contrast" if m["contrast"] < .38 else "medium contrast")
    return d


def contact_sheet(pins: list[Pin], pal: list[str], out: Path, title: str = "", cols: int = 5, width: int = 1500) -> Path:
    """Masonry collage + palette strip. The agent can *look* at this to understand the vibe."""
    gap, col_w = 10, (width - 10 * 6) // cols
    heights = [gap] * cols
    tiles: list[tuple[Image.Image, int, int]] = []
    for p in pins:
        if not p.local_path or not Path(p.local_path).exists():
            continue
        try:
            im = ImageOps.exif_transpose(Image.open(p.local_path)).convert("RGB")
        except Exception:  # noqa: BLE001
            continue
        h = int(im.height * col_w / max(1, im.width))
        h = min(h, int(col_w * 2))
        im = ImageOps.fit(im, (col_w, h))
        c = heights.index(min(heights))
        tiles.append((im, gap + c * (col_w + gap), heights[c]))
        heights[c] += h + gap
    grid_h = max(heights) if tiles else 400
    head, strip = 90, 120
    sheet = Image.new("RGB", (width, head + grid_h + strip), "#F7F5F2")
    for im, x, y in tiles:
        sheet.paste(im, (x, head + y))
    d = ImageDraw.Draw(sheet)
    from .compose.text import font
    d.text((gap * 2, 26), (title or "moodboard").upper(), fill="#1E1B18", font=font("SpaceGrotesk", 34, 600))
    y0 = head + grid_h
    sw = width // max(1, len(pal))
    for i, c in enumerate(pal):
        d.rectangle([i * sw, y0, (i + 1) * sw, y0 + strip], fill=c)
        lum = sum(rgb_of(c)) / 3
        d.text((i * sw + 16, y0 + strip - 40), c, fill="#111" if lum > 140 else "#FFF", font=font("SpaceGrotesk", 22, 500))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=90)
    return out


def build_moodboard(query: str, pins: list[Pin], out_dir: Path | None = None, k: int = 6) -> Moodboard:
    imgs = [im for im in (_load(p) for p in pins) if im is not None]
    pal, weights = palette(imgs, k)
    if not pal:  # no images downloaded — fall back to Pinterest's dominant_color hints
        pal = [c for c in dict.fromkeys(p.dominant_color for p in pins if p.dominant_color)][:k]
        weights = [round(1 / max(1, len(pal)), 3)] * len(pal)
    m = metrics(imgs)
    kws = keywords(pins)
    scores = score_aesthetics(pal, m, kws, query)
    ratios = [p.height / p.width for p in pins if p.width and p.height] or [im.height / im.width for im in imgs]
    portrait = sum(r > 1.1 for r in ratios)
    landscape = sum(r < .9 for r in ratios)
    orient = "portrait" if portrait >= max(landscape, len(ratios) / 3) else "landscape" if landscape > portrait else "square"
    mb = Moodboard(query=query, pins=pins, palette=pal, palette_weights=weights, keywords=kws,
                   aesthetic=next(iter(scores)), aesthetic_scores=dict(list(scores.items())[:5]),
                   orientation=orient, descriptors=describe(m), **m)
    if out_dir:
        mb.contact_sheet = str(contact_sheet(pins, pal, Path(out_dir) / "moodboard.jpg", query))
    return mb
