"""Typography helpers: bundled OFL fonts, variable weights, auto-fit and wrapping."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import ImageDraw, ImageFont

from ..config import FONT_DIR

ALIASES = {"serif": "PlayfairDisplay", "display": "DMSerifDisplay", "sans": "Inter", "grotesk": "SpaceGrotesk",
           "condensed": "BebasNeue", "script": "Caveat", "hand": "Caveat", "elegant": "Italiana",
           "italic": "CormorantGaramond-Italic", "heavy": "ArchivoBlack", "wide": "Syne"}


def font_path(name: str) -> str:
    name = ALIASES.get(name, name)
    p = Path(name)
    if p.suffix and p.exists():
        return str(p)
    f = FONT_DIR / f"{name}.ttf"
    if f.exists():
        return str(f)
    return str(FONT_DIR / "Inter.ttf")


@lru_cache(maxsize=256)
def font(name: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(font_path(name), max(6, int(size)))
    if weight:
        try:
            axes = f.get_variation_axes()
            vals = []
            for ax in axes:
                n = ax.get("name", b"")
                n = n.decode() if isinstance(n, bytes) else str(n)
                if n.lower().startswith("weight"):
                    vals.append(max(ax["minimum"], min(ax["maximum"], weight)))
                elif n.lower().startswith("optical"):
                    vals.append(max(ax["minimum"], min(ax["maximum"], size / 2)))
                else:
                    vals.append(ax.get("default", ax["minimum"]))
            f.set_variation_by_axes(vals)
        except (OSError, AttributeError, KeyError):
            pass  # static font
    return f


def text_size(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, spacing: float = 0) -> tuple[int, int]:
    if not text:
        return 0, 0
    if spacing:
        w = sum(d.textlength(ch, font=f) for ch in text) + spacing * (len(text) - 1)
        b = d.textbbox((0, 0), text, font=f)
        return int(w), b[3] - b[1]
    b = d.textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1]


def wrap(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            trial = f"{cur} {word}".strip()
            if d.textlength(trial, font=f) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def fit(d: ImageDraw.ImageDraw, text: str, name: str, max_w: int, max_h: int, start: int, weight: int | None = None,
        line_h: float = 1.05, min_size: int = 14) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """Largest size where wrapped text fits the box. Returns (font, lines, line_height_px)."""
    size = start
    while size >= min_size:
        f = font(name, size, weight)
        lines = wrap(d, text, f, max_w)
        lh = int(size * line_h)
        if len(lines) * lh <= max_h and all(d.textlength(ln, font=f) <= max_w for ln in lines):
            return f, lines, lh
        size = int(size * 0.93)
    f = font(name, min_size, weight)
    return f, wrap(d, text, f, max_w), int(min_size * line_h)


def draw_lines(d: ImageDraw.ImageDraw, xy: tuple[int, int], lines: list[str], f: ImageFont.FreeTypeFont, lh: int,
               fill, align: str = "left", box_w: int = 0, tracking: float = 0, shadow=None) -> int:
    """Draw wrapped lines; returns the y after the last line."""
    x0, y = xy
    for ln in lines:
        w, _ = text_size(d, ln, f, tracking)
        x = x0 + (box_w - w) // 2 if align == "center" else x0 + box_w - w if align == "right" else x0
        if tracking:
            cx = x
            for ch in ln:
                if shadow:
                    d.text((cx + 2, y + 3), ch, font=f, fill=shadow)
                d.text((cx, y), ch, font=f, fill=fill)
                cx += d.textlength(ch, font=f) + tracking
        else:
            if shadow:
                d.text((x + 2, y + 3), ln, font=f, fill=shadow)
            d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y
