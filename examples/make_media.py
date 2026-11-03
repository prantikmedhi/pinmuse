"""Render README media (hero banner, pipeline diagram, moodboard demo) from the sample gallery."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pinmuse import analyze, pinterest  # noqa: E402
from pinmuse.compose import effects as fx  # noqa: E402
from pinmuse.compose.text import draw_lines, font  # noqa: E402

# README media prefers the AI-rendered showcase in outputs/, and falls back to the offline gallery.
G = ROOT / "outputs" if (ROOT / "outputs" / "neon-poster.jpg").exists() else ROOT / "examples" / "gallery"
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
    names = [n for n in ["old-money-magazine", "ceramics-open-studio", "book-club-story"]
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


def pipeline() -> None:
    W, H = 2400, 520
    bg = Image.new("RGB", (W, H), "#F7F4EF")
    d = ImageDraw.Draw(bg)
    steps = [("01", "Explore", "search · pin · board\nrelated pins · trends"),
             ("02", "Distill", "palette · light · warmth\nmotifs · aesthetic match"),
             ("03", "Prompt", "subject + direction\n+ space for type"),
             ("04", "Generate", "OpenAI · Gemini · Flux\nComfyUI · A1111 · any CLI"),
             ("05", "Compose", "10 templates · real fonts\ngrain · safe zones"),
             ("06", "Ship", "post · caption\nhashtags · pin credits")]
    cols = ["#1E1B18", "#5C4A3A", "#A68A6D", "#9E2B4A", "#2C7DA0", "#6E7F5C"]
    bw, gap, x0 = 340, 52, 70
    for i, ((n, t, sub), c) in enumerate(zip(steps, cols)):
        x = x0 + i * (bw + gap)
        d.rounded_rectangle([x, 90, x + bw, 430], 34, fill=c)
        d.text((x + 36, 120), n, font=font("SpaceGrotesk", 34, 600), fill="#F7F4EF")
        d.text((x + 34, 190), t, font=font("PlayfairDisplay", 66, 700), fill="#F7F4EF")
        draw_lines(d, (x + 36, 300), sub.split("\n"), font("Inter", 23, 500), 36, "#EDE6DC")
        if i < len(steps) - 1:
            ax = x + bw + 8
            d.polygon([(ax + 4, 245), (ax + gap - 12, 260), (ax + 4, 275)], fill="#1E1B18")
    bg.save(M / "pipeline.jpg", quality=92)


def gallery_strip() -> None:
    names = ["neon-poster", "pastel-carousel-1", "vaporwave-story", "dark-academia-quote", "cottage-palette",
             "brutalist-swiss", "old-money-magazine", "y2k-story"]
    W, Hh = 2400, 760
    bg = Image.new("RGBA", (W, Hh), (247, 244, 239, 255))
    x = 40
    for n in names:
        im = Image.open(G / f"{n}.jpg").convert("RGB")
        h = 680
        im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        if x + im.width > W - 40:
            break
        tile = fx.rounded(im, 20)
        bg.alpha_composite(tile, (x, 40))
        x += im.width + 24
    bg.convert("RGB").save(M / "gallery-strip.jpg", quality=90)


def social_preview() -> None:
    """1280×640 GitHub social preview (Settings → General → Social preview)."""
    hero(1280 * 2, 640 * 2, "social-preview.jpg")
    im = Image.open(M / "social-preview.jpg")
    im.resize((1280, 640), Image.LANCZOS).save(M / "social-preview.jpg", quality=92)


def moodboard_demo() -> None:
    pins, _ = pinterest.explore(str(G), 40, "local:" + str(G))
    mb = analyze.build_moodboard("sample gallery (local folder source)", pins, M)
    (M / "moodboard.jpg").rename(M / "moodboard-demo.jpg")
    print("aesthetic:", mb.aesthetic, mb.palette)


if __name__ == "__main__":
    hero()
    pipeline()
    gallery_strip()
    social_preview()
    moodboard_demo()
    print("media written to", M)
