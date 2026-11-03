"""Render README media (hero banner and social preview) from the showcase in outputs/."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pinmuse.compose import effects as fx  # noqa: E402
from pinmuse.compose.text import font  # noqa: E402

# README media prefers the AI-rendered showcase in outputs/, and falls back to the offline gallery.
G = ROOT / "outputs" if (ROOT / "outputs" / "jellyfish-story.jpg").exists() else ROOT / "examples" / "gallery"
M = ROOT / "docs" / "media"
M.mkdir(parents=True, exist_ok=True)


def card(path: str, w: int, radius: int = 22) -> Image.Image:
    im = Image.open(path).convert("RGB")
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return fx.rounded(im, radius)


def shadowed(canvas: Image.Image, im: Image.Image, xy, angle: float = 0) -> None:
    pad = 60
    layer = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 18, pad + im.width, pad + im.height + 18], 26, fill=(0, 0, 0, 120))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    layer.alpha_composite(im, (pad, pad))
    layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    canvas.alpha_composite(layer, (int(xy[0] - layer.width / 2), int(xy[1] - layer.height / 2)))


def hero(W: int = 2400, H: int = 1200, out: str = "hero.jpg") -> None:
    """Editorial banner: paper ground, serif wordmark, a straight row of real outputs. No glows, no tilt."""
    k = H / 1200
    paper, ink, soft, rule = "#F5F1EA", "#1B1714", "#6E655C", "#D9D1C5"
    bg = Image.new("RGB", (W, H), paper)
    d = ImageDraw.Draw(bg)
    m = int(110 * k)
    # right half: story-format outputs (9:16), so nothing is cropped
    names = [n for n in ["fizz-story", "glass-koi", "jellyfish-story"]
             if (G / f"{n}.jpg").exists()][:3]
    gap = int(16 * k)
    tw = min(int((H - 2 * m) * 9 / 16), int((W * .54 - gap * (len(names) - 1)) / len(names)))
    th = int(tw * 16 / 9)
    x = W - m - tw * len(names) - gap * (len(names) - 1)
    split, y0 = x, (H - th) // 2
    for n in names:
        bg.paste(ImageOps.fit(Image.open(G / f"{n}.jpg").convert("RGB"), (tw, th), Image.LANCZOS), (x, y0))
        x += tw + gap
    # left: type
    L = m
    d.text((L, m), "OPEN SOURCE  ·  AGENT SKILL  ·  CLI  ·  MCP", font=font("SpaceGrotesk", int(24 * k), 600), fill=soft)
    d.text((L - 6 * k, m + 150 * k), "pinmuse", font=font("PlayfairDisplay", int(176 * k), 700), fill=ink)
    lines = ["Your AI agent studies Pinterest,", "then designs the post."]
    for i, ln in enumerate(lines):
        d.text((L, m + 420 * k + i * 70 * k), ln, font=font("Inter", int(50 * k), 500), fill=ink)
    d.text((L, m + 600 * k), "Posters, stories and carousels with real typography.", font=font("Inter", int(30 * k), 400), fill=soft)
    d.text((L, m + 646 * k), "Works with any image model, or none.", font=font("Inter", int(30 * k), 400), fill=soft)
    y = H - m - 40 * k
    d.line([L, y - 30 * k, split - 80 * k, y - 30 * k], fill=rule, width=max(1, int(2 * k)))
    d.text((L, y), "github.com/prantikmedhi/pinmuse", font=font("SpaceGrotesk", int(26 * k), 500), fill=ink)
    bg.save(M / out, quality=92)


def social_preview() -> None:
    """1280×640 GitHub social preview (Settings → General → Social preview)."""
    hero(1280 * 2, 640 * 2, "social-preview.jpg")
    im = Image.open(M / "social-preview.jpg")
    im.resize((1280, 640), Image.LANCZOS).save(M / "social-preview.jpg", quality=92)


if __name__ == "__main__":
    hero()
    social_preview()
    print("media written to", M)
