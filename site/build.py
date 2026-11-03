"""Build the static site from outputs/: WebP images + site/_template.html -> site/index.html.

    python site/build.py
"""

from __future__ import annotations

import random
from html import escape
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "outputs"
IMG = SITE / "img"

# single designs: (file, alt, label)
WORK = [
    ("moon-desert", "Surreal desert film poster with a giant moon", "poster · pin"),
    ("old-money-magazine", "Old money magazine cover Instagram story", "magazine · story"),
    ("jellyfish-story", "Bioluminescent jellyfish aquarium story", "story"),
    ("croissant-launch", "Bakery croissant launch Instagram post", "poster · post"),
    ("neon-poster", "Cyberpunk neon Tokyo Pinterest poster", "poster · pin"),
    ("ceramics-open-studio", "Pottery workshop Instagram story", "magazine · story"),
    ("iceland-swiss", "Iceland travel journal swiss poster", "swiss · post"),
    ("jazz-night", "Jazz night event poster", "poster · pin"),
    ("flower-burst", "Exploding flower petals florist post", "minimal · post"),
    ("vaporwave-story", "Vaporwave rooftop party Instagram story", "story"),
    ("perfume-launch", "Perfume launch minimal pin", "minimal · pin"),
    ("book-club-story", "Dark academia book club story", "story"),
    ("record-store", "Record store day swiss poster", "swiss · post"),
    ("matcha-menu", "Matcha cafe menu Instagram post", "minimal · post"),
    ("ski-chalet", "Alpine chalet magazine story", "magazine · story"),
    ("autumn-recipe", "Autumn apple tart recipe pin", "poster · pin"),
    ("desert-roadtrip", "Desert road trip polaroid", "polaroid · post"),
    ("gothic-poster", "Gothic candle product poster", "poster · post"),
    ("boho-minimal", "Terracotta ceramics minimal post", "minimal · post"),
    ("coastal-polaroid", "Amalfi summer polaroid", "polaroid · post"),
    ("clean-girl-poster", "Beauty routine poster", "poster · post"),
    ("dark-academia-quote", "Borges quote card", "quote · post"),
    ("brutalist-swiss", "Brutalist exhibition poster", "swiss · post"),
    ("luxe-collage", "Quiet luxury story", "poster · story"),
    ("y2k-story", "Y2K product drop story", "story"),
    ("cottage-palette", "Cottagecore colour palette pin", "palette · pin"),
]

DECKS = [
    ("unreal-places", "Places that look unreal", "travel · moody film"),
    ("neon-photo-tips", "Shoot the city at night", "how-to · cyberpunk neon"),
    ("coffee-guide", "Better coffee at home", "guide · earthy boho"),
    ("gothic-reading", "Books for long dark nights", "list · dark academia"),
    ("brutalist-guide", "Concrete, but make it beautiful", "architecture · brutalist"),
    ("y2k-drop", "The chrome drop", "product · y2k"),
    ("pastel-carousel", "Make your room feel like a dream", "tips · pastel dream"),
]

# the scroll story: pins → moodboard → palette → photo → finished post
STORY_RAW, STORY_FINAL = "neon-poster", "neon-poster"
STORY_PINS = ["neon-photo-tips-slide-1", "jellyfish-story", "neon-photo-tips", "vaporwave-story", "neon-photo-tips-slide-2",
              "y2k-drop-slide-2", "neon-photo-tips-slide-4", "neon-photo-tips-slide-3", "unreal-places-slide-2"]


def webp(src: Path, name: str, width: int, q: int = 80) -> tuple[str, int, int]:
    im = Image.open(src).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(IMG / f"{name}.webp", "WEBP", quality=q, method=6)
    return f"img/{name}.webp", im.width, im.height


def palette(src: Path, n: int = 8) -> list[str]:
    """Eight median-cut colours, then five spread across the light range so the strip reads as a palette."""
    im = Image.open(src).convert("RGB").resize((96, 96)).quantize(n, method=Image.Quantize.MEDIANCUT)
    pal = im.getpalette()[: n * 3]
    cols = sorted((tuple(pal[i:i + 3]) for i in range(0, n * 3, 3)), key=lambda c: sum(c))
    return ["#%02X%02X%02X" % cols[i] for i in (0, 2, 4, 6, 7)]


def photo(name: str) -> Path:
    return OUT / "photos" / f"{name}.jpg"


def main() -> None:
    IMG.mkdir(exist_ok=True)
    for f in IMG.glob("*.webp"):
        f.unlink()
    parts: dict[str, str] = {}

    # gallery
    tiles = []
    for i, (name, alt, label) in enumerate(w for w in WORK if (OUT / f"{w[0]}.jpg").exists()):
        src, w, h = webp(OUT / f"{name}.jpg", name, 720)
        tiles.append(f'<figure class="tile reveal" style="--i:{i % 4}"><button type="button" data-lb="{i}" '
                     f'aria-label="Open {escape(alt)}"><img src="{src}" width="{w}" height="{h}" alt="{escape(alt)}" '
                     f'loading="lazy" decoding="async"></button><figcaption>{label}</figcaption></figure>')
    parts["gallery"] = "\n".join(tiles)

    # carousels
    decks = []
    for d, (name, title, tag) in enumerate(DECKS):
        frames = sorted(OUT.glob(f"{name}-[0-9]*.jpg"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
        if not frames:
            continue
        slides = []
        for n, f in enumerate(frames, 1):
            what = "cover" if n == 1 else "end card" if n == len(frames) else f"slide {n - 1}"
            src, w, h = webp(f, f.stem, 640)
            slides.append(f'<li><img src="{src}" width="{w}" height="{h}" alt="{escape(title)}, {what}" '
                          f'loading="lazy" decoding="async" draggable="false"></li>')
        dots = "".join(f'<i{" class=on" if k == 0 else ""}></i>' for k in range(len(frames)))
        decks.append(f'''<article class="deck reveal" style="--i:{d % 3}">
  <div class="deck-frame"><ul class="deck-track" tabindex="0" aria-label="{escape(title)} carousel, {len(frames)} slides">{"".join(slides)}</ul>
  <button class="deck-nav prev" type="button" aria-label="Previous slide">‹</button><button class="deck-nav next" type="button" aria-label="Next slide">›</button>
  <span class="deck-count">1/{len(frames)}</span></div>
  <div class="deck-meta"><div><h3>{escape(title)}</h3><p>{tag}</p></div><div class="dots">{dots}</div></div>
</article>''')
    parts["decks"] = "\n".join(decks)

    # raw photos marquee (two rows)
    shots = sorted(p for p in (OUT / "photos").glob("*.jpg"))
    rnd = random.Random(7)
    rnd.shuffle(shots)
    rows = [shots[::2], shots[1::2]]
    marquee = []
    for r, row in enumerate(rows):
        imgs = []
        for p in row:
            src, w, h = webp(p, f"raw-{p.stem}", 420, 72)
            imgs.append(f'<img src="{src}" width="{w}" height="{h}" alt="" loading="lazy" decoding="async">')
        strip = "".join(imgs)
        marquee.append(f'<div class="mq-row{" rev" if r else ""}"><div class="mq-inner">{strip}{strip}</div></div>')
    parts["photos"] = "\n".join(marquee)
    parts["photo_count"] = str(len(shots))

    # hero wall: 6 columns of pins, duplicated for a seamless loop
    pool = [p for p in shots]
    rnd.shuffle(pool)
    cols = []
    for c in range(6):
        col = pool[c::6][:8]
        imgs = "".join(f'<img src="img/raw-{p.stem}.webp" alt="" decoding="async"{" fetchpriority=low" if c > 2 else ""}>'
                       for p in col)
        cols.append(f'<div class="wall-col" style="--d:{70 + c * 9}s;--o:{-c * 7}%">'
                    f'<div class="wall-inner{" up" if c % 2 else ""}">{imgs}{imgs}</div></div>')
    parts["wall"] = "\n".join(cols)

    # scroll story
    pins = []
    for k, n in enumerate(STORY_PINS):
        src = photo(n) if photo(n).exists() else OUT / f"{n}.jpg"
        s, _, _ = webp(src, f"pin-{k}", 300, 72)
        pins.append(f'<img class="pin" data-k="{k}" src="{s}" alt="" decoding="async">')
    parts["pins"] = "".join(pins)
    raw, _, _ = webp(photo(STORY_RAW), "story-raw", 900)
    fin, _, _ = webp(OUT / f"{STORY_FINAL}.jpg", "story-final", 900)
    parts["story_raw"], parts["story_final"] = raw, fin
    parts["swatches"] = "".join(f'<span style="--c:{c}"><em>{c}</em></span>' for c in palette(photo(STORY_RAW)))

    # social card
    Image.open(ROOT / "docs" / "media" / "social-preview.jpg").save(SITE / "og.jpg", quality=88)

    html = (SITE / "_template.html").read_text()
    for k, v in parts.items():
        html = html.replace("{{" + k + "}}", v)
    (SITE / "index.html").write_text(html)
    print(f"{len(tiles)} designs, {len(decks)} carousels, {len(shots)} photos")


if __name__ == "__main__":
    main()
