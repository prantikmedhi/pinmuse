"""Finishing effects that make a render feel shot, printed and posted — not generated."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


def grain(img: Image.Image, amount: float = 0.05, seed: int = 7) -> Image.Image:
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    n = rng.normal(0, 255 * amount, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def vignette(img: Image.Image, strength: float = 0.45) -> Image.Image:
    w, h = img.size
    y, x = np.ogrid[-1:1:h * 1j, -1:1:w * 1j]
    mask = 1 - strength * np.clip((x ** 2 + y ** 2) / 2, 0, 1) ** 1.2
    a = np.asarray(img.convert("RGB")).astype(np.float32) * mask[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def lightleak(img: Image.Image, color=(255, 140, 60), strength: float = 0.35, corner: str = "tr") -> Image.Image:
    w, h = img.size
    leak = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(leak)
    cx = w * (.95 if "r" in corner else .05)
    cy = h * (.05 if "t" in corner else .95)
    r = max(w, h) * .55
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(255 * strength))
    leak = leak.filter(ImageFilter.GaussianBlur(max(w, h) * .12))
    return Image.composite(Image.blend(img.convert("RGB"), Image.new("RGB", (w, h), color), .6), img.convert("RGB"), leak)


def scanlines(img: Image.Image, gap: int = 4, alpha: int = 28) -> Image.Image:
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for y in range(0, img.height, gap):
        d.line([0, y, img.width, y], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")


def duotone(img: Image.Image, dark: str, light: str) -> Image.Image:
    return ImageOps.colorize(ImageOps.grayscale(img), dark, light).convert("RGB")


def scrim(img: Image.Image, top: float = 0.0, bottom: float = 0.45, color=(0, 0, 0), max_alpha: int = 190) -> Image.Image:
    """Gradient darkening so type stays legible over any photo."""
    w, h = img.size
    a = np.zeros(h, np.float32)
    if bottom:
        start = int(h * (1 - bottom))
        a[start:] = np.linspace(0, 1, h - start) ** 1.4
    if top:
        end = int(h * top)
        a[:end] = np.maximum(a[:end], np.linspace(1, 0, end) ** 1.4)
    mask = Image.fromarray((np.tile(a[:, None], (1, w)) * max_alpha).astype(np.uint8))
    return Image.composite(Image.new("RGB", (w, h), color), img.convert("RGB"), mask)


def glass(img: Image.Image, box: tuple[int, int, int, int], radius: int = 36, tint=(255, 255, 255), alpha: int = 70,
          blur: int = 28) -> Image.Image:
    """Frosted-glass panel (iOS widget look)."""
    img = img.convert("RGB")
    region = img.crop(box).filter(ImageFilter.GaussianBlur(blur))
    region = Image.blend(region, Image.new("RGB", region.size, tint), alpha / 255)
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, region.width - 1, region.height - 1], radius=radius, fill=255)
    img.paste(region, box[:2], mask)
    return img


def rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def apply(img: Image.Image, names: list[str] | tuple[str, ...], palette: list[str] | None = None) -> Image.Image:
    for n in names:
        if n == "grain":
            img = grain(img, 0.035)
        elif n == "vignette":
            img = vignette(img, 0.4)
        elif n == "lightleak":
            img = lightleak(img)
        elif n == "scanlines":
            img = scanlines(img)
        elif n == "duotone" and palette and len(palette) >= 2:
            img = duotone(img, palette[-1], palette[0])
    return img
