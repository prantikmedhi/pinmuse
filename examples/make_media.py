"""Render README media (hero banner, pipeline diagram, moodboard demo) from the sample gallery."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

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


def hero() -> None:
    W, H = 2400, 1100
    bg = Image.new("RGB", (W, H), "#0F0D0C")
    # aura
    aura = Image.new("RGB", (W // 4, H // 4), "#0F0D0C")
    d = ImageDraw.Draw(aura)
    for (x, y, r, c) in [(120, 60, 130, "#5B1A2E"), (420, 220, 160, "#2D0B59"), (560, 40, 120, "#7A5C3E")]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    bg = Image.blend(bg, aura.filter(ImageFilter.GaussianBlur(60)).resize((W, H)), .9)
    bg = fx.grain(bg, .03).convert("RGBA")
    picks = [("neon-poster", -9, 1400, 600), ("dark-academia-quote", -3, 1640, 520), ("vaporwave-story", 4, 1880, 560),
             ("old-money-magazine", 10, 2130, 600), ("coastal-polaroid", -6, 1700, 860)]
    for name, ang, x, y in picks[:4]:
        shadowed(bg, card(str(G / f"{name}.jpg"), 330), (x, y), ang)
    d = ImageDraw.Draw(bg)
    d.text((140, 250), "pinmuse", font=font("PlayfairDisplay", 210, 800), fill="#F5EFE6")
    d.text((148, 520), "Your AI agent explores Pinterest by itself", font=font("Inter", 50, 600), fill="#F5EFE6")
    d.text((148, 590), "and makes aesthetic posters, stories & posts.", font=font("Inter", 50, 400), fill="#CBBFB0")
    tags = ["Claude Code", "Codex", "Gemini CLI", "Antigravity", "opencode", "OpenClaw", "Hermes", "MCP"]
    x, y = 148, 720
    f = font("SpaceGrotesk", 30, 600)
    for t in tags:
        tw = d.textlength(t, font=f)
        if x + tw + 56 > 1080:
            x, y = 148, y + 74
        d.rounded_rectangle([x, y, x + tw + 44, y + 56], 28, outline="#F5EFE6", width=2)
        d.text((x + 22, y + 10), t, font=f, fill="#F5EFE6")
        x += tw + 60
    d.text((148, 930), "no screenshots  ·  any image model  ·  14 aesthetics  ·  10 templates  ·  15 formats",
           font=font("SpaceGrotesk", 28, 500), fill="#9C8F80")
    bg.convert("RGB").save(M / "hero.jpg", quality=90)


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
    W, H = 1280, 640
    hero = Image.open(M / "hero.jpg").convert("RGB")
    hero = hero.resize((W, round(hero.height * W / hero.width)), Image.LANCZOS)
    bg = Image.new("RGB", (W, H), "#0F0D0C")
    bg.paste(hero, (0, (H - hero.height) // 2))
    bg.save(M / "social-preview.jpg", quality=92)


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
