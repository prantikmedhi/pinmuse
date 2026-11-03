"""Build the static site: copy outputs/ as WebP and fill the gallery into index.html.

    python site/build.py
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
IMG = SITE / "img"

# (file, alt, label)
WORK = [
    ("old-money-magazine", "Old money magazine cover Instagram story", "magazine · story"),
    ("neon-poster", "Cyberpunk neon Tokyo Pinterest poster", "poster · pin"),
    ("ceramics-open-studio", "Pottery workshop Instagram story", "magazine · story"),
    ("croissant-launch", "Bakery croissant launch Instagram post", "poster · post"),
    ("jazz-night", "Jazz night event poster", "poster · pin"),
    ("vaporwave-story", "Vaporwave rooftop party Instagram story", "story"),
    ("matcha-menu", "Matcha cafe menu Instagram post", "minimal · post"),
    ("perfume-launch", "Perfume launch minimal pin", "minimal · pin"),
    ("book-club-story", "Dark academia book club story", "story"),
    ("record-store", "Record store day swiss poster", "swiss · post"),
    ("autumn-recipe", "Autumn apple tart recipe pin", "poster · pin"),
    ("desert-roadtrip", "Desert road trip polaroid", "polaroid · post"),
    ("ski-chalet", "Alpine chalet magazine story", "magazine · story"),
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


def webp(src: Path, dst: Path, width: int) -> tuple[int, int]:
    im = Image.open(src).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=82, method=6)
    return im.size


def main() -> None:
    IMG.mkdir(exist_ok=True)
    tiles = []
    for name, alt, label in WORK:
        src = ROOT / "outputs" / f"{name}.jpg"
        if not src.exists():
            continue
        w, h = webp(src, IMG / f"{name}.webp", 720)
        tiles.append(f'<figure><img src="img/{name}.webp" width="{w}" height="{h}" alt="{alt}" loading="lazy" '
                     f'decoding="async"><figcaption>{label}</figcaption></figure>')
    for i in range(1, 6):
        webp(ROOT / "outputs" / f"pastel-carousel-{i}.jpg", IMG / f"carousel-{i}.webp", 540)
    photos = sorted((ROOT / "outputs" / "photos").glob("*.jpg"))
    shots = []
    for p in photos:
        w, h = webp(p, IMG / f"photo-{p.stem}.webp", 720)
        shots.append(f'<img src="img/photo-{p.stem}.webp" width="{w}" height="{h}" alt="AI generated photo: '
                     f'{p.stem.replace("-", " ")}" loading="lazy" decoding="async">')
    Image.open(ROOT / "docs" / "media" / "social-preview.jpg").save(SITE / "og.jpg", quality=88)
    html = (SITE / "index.html").read_text()
    html = re.sub(r"(<!-- gallery -->).*?(<!-- /gallery -->)", lambda m: m[1] + "\n" + "\n".join(tiles) + "\n" + m[2],
                  html, flags=re.S)
    html = re.sub(r"(<!-- photos -->).*?(<!-- /photos -->)", lambda m: m[1] + "\n" + "\n".join(shots) + "\n" + m[2],
                  html, flags=re.S)
    (SITE / "index.html").write_text(html)
    print(len(tiles), "designs,", len(shots), "photos")


if __name__ == "__main__":
    main()
