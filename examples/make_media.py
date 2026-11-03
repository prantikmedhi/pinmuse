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


def hero(W: int = 2400, H: int = 1100, out: str = "hero.jpg") -> None:
    """Cozy banner: oat ground, terracotta and sage glow, cocoa ink, warm cards. Scales to any size."""
    k = H / 1100
    bg = Image.new("RGB", (W, H), "#F3E9DC")
    aura = Image.new("RGB", (W // 4, H // 4), "#F3E9DC")
    d = ImageDraw.Draw(aura)
    for (x, y, r, c) in [(.06, .1, .14, "#E8B79A"), (.55, .95, .2, "#C9D2B4"), (.92, .15, .16, "#E9C9A8"),
                         (.3, .9, .1, "#EED6C4")]:
        cx, cy, rr = x * W / 4, y * H / 4, r * W / 4
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c)
    bg = Image.blend(bg, aura.filter(ImageFilter.GaussianBlur(70 * k)).resize((W, H)), .85)
    bg = fx.grain(bg, .025).convert("RGBA")
    picks = [("dark-academia-quote", -8, .585, .55), ("boho-minimal", -2, .69, .47), ("coastal-polaroid", 5, .795, .53),
             ("luxe-collage", 11, .88, .56)]
    for name, ang, x, y in picks:
        shadowed(bg, card(str(G / f"{name}.jpg"), int(330 * k)), (x * W, y * H), ang)
    ink, soft, mute = "#3B2A20", "#6B4E3D", "#9A7B66"
    d = ImageDraw.Draw(bg)
    L = int(.058 * W) if W / H < 2.1 else 140
    d.text((L, 250 * k), "pinmuse", font=font("PlayfairDisplay", int(210 * k), 800), fill=ink)
    d.text((L + 8 * k, 520 * k), "Your AI agent explores Pinterest by itself", font=font("Inter", int(48 * k), 600), fill=ink)
    d.text((L + 8 * k, 586 * k), "and makes aesthetic posters, stories & posts.", font=font("Inter", int(48 * k), 400), fill=soft)
    tags = ["Claude Code", "Codex", "Gemini CLI", "Antigravity", "opencode", "OpenClaw", "Hermes", "MCP"]
    x, y = L + 8 * k, 715 * k
    f = font("SpaceGrotesk", int(30 * k), 600)
    for t in tags:
        tw = d.textlength(t, font=f)
        if x + tw + 56 * k > W * .45:
            x, y = L + 8 * k, y + 74 * k
        d.rounded_rectangle([x, y, x + tw + 44 * k, y + 56 * k], 28 * k, fill="#FBF6EF", outline="#C98F6E", width=2)
        d.text((x + 22 * k, y + 10 * k), t, font=f, fill=ink)
        x += tw + 60 * k
    d.text((L + 8 * k, 930 * k), "no screenshots  ·  any image model  ·  14 aesthetics  ·  10 templates  ·  15 formats",
           font=font("SpaceGrotesk", int(27 * k), 500), fill=mute)
    bg.convert("RGB").save(M / out, quality=92)


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
