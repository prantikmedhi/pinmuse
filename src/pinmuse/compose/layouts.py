"""Templates: poster, magazine, story, quote, polaroid, minimal, swiss, collage, palette, carousel."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from ..formats import Format
from . import effects as fx
from .text import draw_lines, fit, font, text_size, wrap


@dataclass
class Design:
    template: str
    fmt: Format
    images: list[str] = field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    body: str = ""
    kicker: str = ""
    handle: str = ""
    cta: str = ""
    palette: list[str] = field(default_factory=lambda: ["#F3EEE7", "#D9CBB8", "#A68A6D", "#5C4A3A", "#1E1B18"])
    display_font: str = "PlayfairDisplay"
    body_font: str = "Inter"
    effects: tuple[str, ...] = ("grain",)
    slides: list[dict] = field(default_factory=list)  # carousel: [{"title":…, "body":…}]
    logo: str = ""


# ---------- helpers ----------

def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _lum(c) -> float:
    c = _rgb(c) if isinstance(c, str) else c
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def region_lum(img: Image.Image, box) -> float:
    a = np.asarray(img.crop(tuple(int(v) for v in box)).convert("L").resize((32, 32)), dtype=np.float32)
    return float(a.mean())


def ink(pal: list[str], bg_lum: float) -> str:
    """Pick the palette colour that reads best on a background of this luminance."""
    dark = min(pal, key=_lum)
    light = max(pal, key=_lum)
    dark = dark if _lum(dark) < 90 else "#141414"
    light = light if _lum(light) > 200 else "#FAFAF7"
    # WCAG contrast, not a fixed cut-off: mid-tones like hot pink need dark ink
    rel = lambda v: ((v / 255 + .055) / 1.055) ** 2.4  # noqa: E731
    bg = rel(bg_lum)
    ratio = lambda c: (max(rel(_lum(c)), bg) + .05) / (min(rel(_lum(c)), bg) + .05)  # noqa: E731
    return dark if ratio(dark) >= ratio(light) else light


def accent(pal: list[str], against: str | None = None) -> str:
    """Most colourful palette entry; with `against`, the one that also stands out from that background."""
    def score(c):
        sat = max(_rgb(c)) - min(_rgb(c))
        return sat + (abs(_lum(c) - _lum(against)) * 1.5 if against else 0.001 * _lum(c))
    return max(pal, key=score)


def load(path: str | None, size: tuple[int, int], pal: list[str]) -> Image.Image:
    if path and Path(path).exists():
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        return ImageOps.fit(im, size, Image.LANCZOS, centering=(0.5, 0.45))
    # graceful fallback: soft palette gradient
    w, h = size
    a, b = np.array(_rgb(pal[0]), float), np.array(_rgb(pal[min(2, len(pal) - 1)]), float)
    t = np.linspace(0, 1, h)[:, None, None]
    return Image.fromarray(np.broadcast_to(a + (b - a) * t, (h, w, 3)).astype(np.uint8))


def pill(d: ImageDraw.ImageDraw, xy, text: str, f, fg, bg, pad=(28, 14), outline=None) -> tuple[int, int]:
    tw, th = text_size(d, text, f)
    x, y = xy
    asc = f.getbbox(text)[1]
    d.rounded_rectangle([x, y, x + tw + pad[0] * 2, y + th + pad[1] * 2], radius=(th + pad[1] * 2) // 2, fill=bg,
                        outline=outline, width=2 if outline else 0)
    d.text((x + pad[0], y + pad[1] - asc), text, font=f, fill=fg)
    return tw + pad[0] * 2, th + pad[1] * 2


# ---------- templates ----------

def poster(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    img = load(ds.images[0] if ds.images else None, (W, H), ds.palette)
    m = int(W * .07)
    top_lum = region_lum(img, (0, 0, W, H * .4))
    if 80 < top_lum < 175:  # mid-tone sky: add a soft scrim for legibility
        img = fx.scrim(img, top=.45, bottom=0, color=_rgb(min(ds.palette, key=_lum)), max_alpha=120)
        top_lum = 60
    col = ink(ds.palette, top_lum)
    d = ImageDraw.Draw(img)
    y = m
    if ds.kicker:
        f = font(ds.body_font, int(W * .022), 600)
        draw_lines(d, (m, y), [ds.kicker.upper()], f, int(W * .03), col, tracking=W * .006)
        y += int(W * .055)
    if ds.title:
        f, lines, lh = fit(d, ds.title, ds.display_font, W - 2 * m, int(H * .3), int(W * .2), 700, .98)
        y = draw_lines(d, (m, y), lines, f, lh, col)
    if ds.subtitle:
        f, lines, lh = fit(d, ds.subtitle, ds.body_font, int((W - 2 * m) * .8), int(H * .09), int(W * .036), 400, 1.3)
        draw_lines(d, (m, y + int(W * .035)), lines, f, lh, col)
    bot_lum = region_lum(img, (0, H * .88, W, H))
    bcol = ink(ds.palette, bot_lum)
    by = H - m - int(W * .02)
    d.line([m, by - int(W * .025), W - m, by - int(W * .025)], fill=bcol, width=max(1, W // 600))
    f = font(ds.body_font, int(W * .02), 500)
    if ds.handle:
        draw_lines(d, (m, by), [ds.handle], f, 0, bcol, tracking=W * .002)
    if ds.cta:
        draw_lines(d, (m, by), [ds.cta.upper()], f, 0, bcol, align="right", box_w=W - 2 * m, tracking=W * .004)
    return img


def magazine(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    img = load(ds.images[0] if ds.images else None, (W, H), ds.palette)
    m = int(W * .05)
    img = fx.scrim(img, top=.0, bottom=.4, color=(0, 0, 0), max_alpha=150)
    col = ink(ds.palette, region_lum(img, (0, 0, W, H * .2)))
    d = ImageDraw.Draw(img)
    mast = (ds.title or "MUSE").upper()
    size = int(W * .3)
    while size > 20 and d.textlength(mast, font=font(ds.display_font, size, 900)) > W - 2 * m:
        size = int(size * .95)
    f = font(ds.display_font, size, 900)
    lh = int(size * .95)
    draw_lines(d, (m, m), [mast], f, lh, col, align="center", box_w=W - 2 * m)
    if ds.kicker:
        kf = font(ds.body_font, int(W * .02), 600)
        mb_ = d.textbbox((0, 0), mast, font=f)
        draw_lines(d, (m, m + mb_[3] + int(W * .025)), [ds.kicker.upper()], kf, 0, col, align="center",
                   box_w=W - 2 * m, tracking=W * .008)
    light = "#FAFAF7"
    y = int(H * .66)
    if ds.subtitle:
        sf, sl, slh = fit(d, ds.subtitle, "PlayfairDisplay-Italic", int(W * .62), int(H * .14), int(W * .075), 500, 1.0)
        y = draw_lines(d, (m, y), sl, sf, slh, light)
    if ds.body:
        bf = font(ds.body_font, int(W * .026), 500)
        for line in [b.strip() for b in ds.body.split("\n") if b.strip()][:4]:
            d.rectangle([m, y + int(W * .03), m + int(W * .04), y + int(W * .034)], fill=accent(ds.palette))
            y = draw_lines(d, (m, y + int(W * .045)), wrap(d, line.upper(), bf, int(W * .6)), bf, int(W * .034), light)
    if ds.handle:
        hf = font(ds.body_font, int(W * .02), 500)
        draw_lines(d, (m, H - m - int(W * .02)), [ds.handle], hf, 0, light, align="right", box_w=W - 2 * m)
    return img


def story(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    img = load(ds.images[0] if ds.images else None, (W, H), ds.palette)
    img = fx.scrim(img, top=.2, bottom=.55, color=(8, 8, 10), max_alpha=205)
    d = ImageDraw.Draw(img)
    m = int(W * .08)
    top = int(H * max(.12, ds.fmt.safe_top) + W * .02)
    light = "#FFFFFF"
    if ds.kicker:
        f = font(ds.body_font, int(W * .03), 600)
        pill(d, (m, top), ds.kicker.upper(), f, "#111111", "#FFFFFF", pad=(int(W * .03), int(W * .016)))
    bottom = int(H * (1 - max(.18, ds.fmt.safe_bottom)))
    blocks = []
    if ds.cta:
        blocks.append("cta")
    y = bottom
    if ds.cta:
        f = font(ds.body_font, int(W * .033), 600)
        tw, th = text_size(d, ds.cta, f)
        bw = tw + int(W * .1)
        y -= th + int(W * .04)
        pill(d, (m, y), ds.cta, f, "#111111", accent(ds.palette) if _lum(accent(ds.palette)) > 120 else "#FFFFFF",
             pad=(int(W * .05), int(W * .02)))
        _ = bw
        y -= int(W * .07)
    if ds.subtitle:
        f, lines, lh = fit(d, ds.subtitle, ds.body_font, W - 2 * m, int(H * .12), int(W * .042), 400, 1.32)
        y -= len(lines) * lh
        draw_lines(d, (m, y), lines, f, lh, (235, 235, 235))
        y -= int(W * .03)
    if ds.title:
        f, lines, lh = fit(d, ds.title, ds.display_font, W - 2 * m, int(H * .26), int(W * .14), 700, 1.0)
        y -= len(lines) * lh
        draw_lines(d, (m, y), lines, f, lh, light)
    if ds.handle:
        f = font(ds.body_font, int(W * .028), 500)
        draw_lines(d, (m, top), [ds.handle], f, 0, light, align="right", box_w=W - 2 * m)
    return img


def quote(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    if ds.images:
        bg = load(ds.images[0], (W, H), ds.palette).filter(ImageFilter.GaussianBlur(W * .01))
        bg = Image.blend(bg, Image.new("RGB", (W, H), ds.palette[0]), .55)
    else:
        bg = Image.new("RGB", (W, H), ds.palette[0])
    col = ink(ds.palette, region_lum(bg, (0, 0, W, H)))
    d = ImageDraw.Draw(bg)
    m = int(W * .11)
    qf = font("PlayfairDisplay", int(W * .32), 700)
    d.text((m - W * .02, H * .1), "“", font=qf, fill=accent(ds.palette))
    text = ds.title or ds.body
    f, lines, lh = fit(d, text, ds.display_font, W - 2 * m, int(H * .5), int(W * .1), 500, 1.18)
    total = len(lines) * lh
    y = int(H * .5 - total / 2)
    y = draw_lines(d, (m, y), lines, f, lh, col, align="left", box_w=W - 2 * m)
    if ds.subtitle:
        sf = font(ds.body_font, int(W * .026), 500)
        d.line([m, y + W * .05, m + W * .08, y + W * .05], fill=col, width=max(2, W // 400))
        sl = wrap(d, ds.subtitle.upper(), sf, int((W - 2 * m - W * .11) * .9))
        draw_lines(d, (m + int(W * .11), y + int(W * .033)), sl[:3], sf, int(W * .042), col, tracking=W * .003)
    if ds.handle:
        hf = font(ds.body_font, int(W * .024), 500)
        draw_lines(d, (m, H - int(W * .09)), [ds.handle], hf, 0, col)
    return bg


def polaroid(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    bg = Image.new("RGB", (W, H), ds.palette[0])
    bg = fx.grain(bg, .03)
    pw = int(W * .76)
    ph = int(pw * 1.18)
    photo_side = pw - int(pw * .1)
    frame = Image.new("RGB", (pw, ph), "#FBFAF6")
    frame.paste(load(ds.images[0] if ds.images else None, (photo_side, photo_side), ds.palette), (int(pw * .05), int(pw * .05)))
    fd = ImageDraw.Draw(frame)
    cap = ds.subtitle or ds.title
    if cap:
        cf, cl, clh = fit(fd, cap, "Caveat", photo_side, int(ph - photo_side - pw * .1), int(pw * .085), 600, 1.0)
        draw_lines(fd, (int(pw * .05), photo_side + int(pw * .07)), cl[:2], cf, clh, "#2A2622", align="center", box_w=photo_side)
    shadow = Image.new("RGBA", (pw + 80, ph + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([40, 50, pw + 40, ph + 50], fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    angle = -3.2
    card = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    card.alpha_composite(shadow)
    card.paste(frame, (40, 40))
    card = card.rotate(angle, resample=Image.BICUBIC, expand=True)
    x, y = (W - card.width) // 2, int(H * .53 - card.height / 2)
    bg.paste(card, (x, y), card)
    d = ImageDraw.Draw(bg)
    tape = Image.new("RGBA", (int(W * .2), int(W * .055)), _rgb(ds.palette[1]) + (200,))
    tape = tape.rotate(6, expand=True)
    bg.paste(tape, (W // 2 - tape.width // 2, y + int(W * .01)), tape)
    col = ink(ds.palette, _lum(ds.palette[0]))
    if ds.kicker or (ds.title and ds.subtitle):
        tf = font(ds.body_font, int(W * .024), 600)
        draw_lines(d, (0, int(H * .05)), [(ds.kicker or ds.title).upper()], tf, 0, col, align="center", box_w=W,
                   tracking=W * .008)
    if ds.handle:
        hf = font("Caveat", int(W * .045), 600)
        draw_lines(d, (0, H - int(W * .1)), [ds.handle], hf, 0, col, align="center", box_w=W)
    return bg


def minimal(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    bg = Image.new("RGB", (W, H), ds.palette[0])
    m = int(W * .09)
    ih = int(H * .74)
    bg.paste(load(ds.images[0] if ds.images else None, (W - 2 * m, ih - m), ds.palette), (m, m))
    d = ImageDraw.Draw(bg)
    col = ink(ds.palette, _lum(ds.palette[0]))
    y = ih + int(W * .04)
    if ds.title:
        f, lines, lh = fit(d, ds.title, ds.display_font, int((W - 2 * m) * .56), int(H * .12), int(W * .075), 500, 1.05)
        draw_lines(d, (m, y), lines, f, lh, col)
    sf = font(ds.body_font, int(W * .021), 500)
    if ds.kicker:
        draw_lines(d, (m, y + int(W * .01)), [ds.kicker.upper()], sf, 0, col, align="right", box_w=W - 2 * m,
                   tracking=W * .005)
    if ds.subtitle:
        f2 = font(ds.body_font, int(W * .024), 400)
        lines = wrap(d, ds.subtitle, f2, int((W - 2 * m) * .34))
        draw_lines(d, (W - m - int((W - 2 * m) * .34), y + int(W * .05)), lines[:3], f2, int(W * .034), col)
    if ds.handle:
        draw_lines(d, (m, H - int(W * .07)), [ds.handle], sf, 0, col, tracking=W * .002)
    return bg


def swiss(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    bg = Image.new("RGB", (W, H), ds.palette[0])
    split = int(W * .42)
    bg.paste(load(ds.images[0] if ds.images else None, (W - split, H), ds.palette), (split, 0))
    d = ImageDraw.Draw(bg)
    blockc = accent(ds.palette)
    d.rectangle([0, 0, split, H], fill=blockc)
    col = ink(ds.palette, _lum(blockc))
    m = int(W * .05)
    if ds.kicker:
        f = font("SpaceGrotesk", int(W * .022), 600)
        draw_lines(d, (m, m), [ds.kicker.upper()], f, 0, col, tracking=W * .003)
    if ds.title:
        f, lines, lh = fit(d, ds.title.upper(), "ArchivoBlack", split - 2 * m, int(H * .55), int(W * .16), None, .92)
        draw_lines(d, (m, int(H * .2)), lines, f, lh, col)
    if ds.subtitle:
        f, lines, lh = fit(d, ds.subtitle, "SpaceGrotesk", split - 2 * m, int(H * .14), int(W * .03), 500, 1.3)
        draw_lines(d, (m, int(H * .8)), lines, f, lh, col)
    for i in range(1, 4):  # grid ticks
        d.line([split + (W - split) * i / 4, H - m, split + (W - split) * i / 4, H - m + m // 2], fill="#FFFFFF", width=2)
    if ds.handle:
        f = font("SpaceGrotesk", int(W * .02), 500)
        draw_lines(d, (m, H - m - int(W * .02)), [ds.handle], f, 0, col)
    return bg


def collage(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    bg = Image.new("RGB", (W, H), ds.palette[0])
    d = ImageDraw.Draw(bg)
    m, g = int(W * .06), int(W * .02)
    head = int(H * .16) if ds.title else m
    imgs = (ds.images or [None])[:5]
    area = (m, head, W - m, H - m - (int(W * .05) if ds.handle else 0))
    aw, ah = area[2] - area[0], area[3] - area[1]
    n = len(imgs)
    if n == 1:
        boxes = [(0, 0, aw, ah)]
    elif n == 2:
        boxes = [(0, 0, aw // 2 - g // 2, ah), (aw // 2 + g // 2, 0, aw, ah)]
    elif n == 3:
        boxes = [(0, 0, int(aw * .58) - g // 2, ah), (int(aw * .58) + g // 2, 0, aw, ah // 2 - g // 2),
                 (int(aw * .58) + g // 2, ah // 2 + g // 2, aw, ah)]
    else:
        boxes = [(0, 0, aw // 2 - g // 2, int(ah * .55) - g // 2), (aw // 2 + g // 2, 0, aw, int(ah * .45) - g // 2),
                 (0, int(ah * .55) + g // 2, aw // 2 - g // 2, ah), (aw // 2 + g // 2, int(ah * .45) + g // 2, aw, ah)]
        imgs = imgs[:4]
    for p, (x0, y0, x1, y1) in zip(imgs, boxes):
        tile = fx.rounded(load(p, (x1 - x0, y1 - y0), ds.palette), int(W * .015))
        bg.paste(tile, (area[0] + x0, area[1] + y0), tile)
    col = ink(ds.palette, _lum(ds.palette[0]))
    if ds.title:
        f, lines, lh = fit(d, ds.title, ds.display_font, W - 2 * m, head - m - int(W * .01), int(W * .08), 600, 1.0)
        draw_lines(d, (m, m - int(W * .01)), lines[:2], f, lh, col)
    if ds.handle:
        f = font(ds.body_font, int(W * .022), 500)
        draw_lines(d, (m, H - m), [ds.handle], f, 0, col, align="center", box_w=W - 2 * m)
    return bg


def palette_card(ds: Design) -> Image.Image:
    W, H = ds.fmt.width, ds.fmt.height
    bg = Image.new("RGB", (W, H), "#F7F5F1")
    d = ImageDraw.Draw(bg)
    m = int(W * .07)
    col = "#1B1B1B"
    img_h = int(H * .42)
    if ds.images:
        tile = fx.rounded(load(ds.images[0], (W - 2 * m, img_h), ds.palette), int(W * .02))
        bg.paste(tile, (m, m + int(H * .1)), tile)
    tf = font(ds.display_font, int(W * .075), 600)
    draw_lines(d, (m, m - int(W * .01)), [ds.title or "palette"], tf, 0, col)
    if ds.kicker:
        kf = font("SpaceGrotesk", int(W * .022), 600)
        draw_lines(d, (m, m + int(W * .01)), [ds.kicker.upper()], kf, 0, col, align="right", box_w=W - 2 * m,
                   tracking=W * .004)
    y0 = m + int(H * .1) + (img_h + int(W * .04) if ds.images else 0)
    pal = ds.palette[:6]
    sh = (H - y0 - m - int(W * .06)) // max(1, len(pal))
    nf = font("SpaceGrotesk", int(W * .03), 600)
    for i, c in enumerate(pal):
        y = y0 + i * sh
        d.rounded_rectangle([m, y, W - m, y + sh - int(W * .012)], radius=int(W * .015), fill=c)
        tc = "#111111" if _lum(c) > 140 else "#FFFFFF"
        d.text((m + int(W * .03), y + (sh - int(W * .012)) / 2 - W * .02), c.upper(), font=nf, fill=tc)
        rgb = "  ".join(str(v) for v in _rgb(c))
        rf = font("SpaceGrotesk", int(W * .022), 400)
        tw = d.textlength(rgb, font=rf)
        d.text((W - m - int(W * .03) - tw, y + (sh - int(W * .012)) / 2 - W * .014), rgb, font=rf, fill=tc)
    if ds.handle:
        hf = font(ds.body_font, int(W * .022), 500)
        draw_lines(d, (m, H - m - int(W * .01)), [ds.handle], hf, 0, col, align="center", box_w=W - 2 * m)
    return bg


def carousel(ds: Design) -> list[Image.Image]:
    """Cover, then one full-bleed photo slide per tip, then a save/share card."""
    W, H = ds.fmt.width, ds.fmt.height
    slides = [poster(ds)]
    col_bg = ds.palette[0]
    col = ink(ds.palette, _lum(col_bg))
    acc = accent(ds.palette, col_bg)
    num_col = acc if abs(_lum(acc) - _lum(col_bg)) > 70 else col
    total = len(ds.slides) + 2
    m = int(W * .08)
    split = int(H * .58)
    pics = ds.images[1:] or ds.images
    for i, s in enumerate(ds.slides, start=2):
        img = Image.new("RGB", (W, H), col_bg)
        if pics:
            img.paste(load(pics[(i - 2) % len(pics)], (W, split), ds.palette), (0, 0))
        d = ImageDraw.Draw(img)
        pf = font(ds.body_font, int(W * .022), 600)
        # step badge sits on the photo's bottom edge
        badge = f"{i - 1:02d}"
        bf = font(ds.display_font, int(W * .05), 700)
        bw, bh = text_size(d, badge, bf)
        r = int(max(bw, bh) * .95)
        cx, cy = m + r, split
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=num_col)
        d.text((cx, cy), badge, font=bf, fill=ink(ds.palette, _lum(num_col)), anchor="mm")
        y = split + r + int(W * .04)
        f, lines, lh = fit(d, s.get("title", ""), ds.display_font, W - 2 * m, int(H * .12), int(W * .075), 700, 1.04)
        y = draw_lines(d, (m, y), lines, f, lh, col)
        bf2, bl, blh = fit(d, s.get("body", ""), ds.body_font, W - 2 * m, H - y - int(W * .16), int(W * .034), 400, 1.42)
        draw_lines(d, (m, y + int(W * .022)), bl, bf2, blh, col)
        fy = H - int(W * .06)
        draw_lines(d, (m, fy), [f"{i}/{total}"], pf, 0, col, align="right", box_w=W - 2 * m)
        if ds.handle:
            draw_lines(d, (m, fy), [ds.handle], pf, 0, col)
        slides.append(fx.apply(img, ds.effects, ds.palette))
    # end card: the cover photo, blurred and tinted, with the call to action
    base = load(ds.images[0] if ds.images else None, (W, H), ds.palette)
    dark = min(ds.palette, key=_lum)
    tint = Image.new("RGB", (W, H), _rgb(dark if _lum(dark) < 70 else "#16130F"))
    end = Image.blend(base.filter(ImageFilter.GaussianBlur(W * .03)), tint, .62)
    d = ImageDraw.Draw(end)
    ecol = "#FAFAF7"
    f, lines, lh = fit(d, ds.cta or "Save this for later", ds.display_font, int(W * .8), int(H * .4), int(W * .12), 700, 1.0)
    y = int(H / 2 - len(lines) * lh / 2)
    draw_lines(d, (int(W * .1), y), lines, f, lh, ecol, align="center", box_w=int(W * .8))
    hf = font(ds.body_font, int(W * .026), 600)
    draw_lines(d, (0, int(H * .8)), ["SAVE  ·  SHARE  ·  FOLLOW" + (f"  {ds.handle}" if ds.handle else "")], hf, 0, ecol,
               align="center", box_w=W, tracking=W * .003)
    slides.append(fx.apply(end, ds.effects, ds.palette))
    return slides


TEMPLATES = {"poster": poster, "magazine": magazine, "story": story, "quote": quote, "polaroid": polaroid,
             "minimal": minimal, "swiss": swiss, "collage": collage, "palette": palette_card, "carousel": carousel}
