"""Render the README gallery. Fully offline: procedural provider, no API key, no network.

    python examples/make_samples.py

With a real model configured (e.g. OPENAI_API_KEY) pass --provider openai and --inspo to get
Pinterest-informed photographic results instead of generative art.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pinmuse.pipeline import create  # noqa: E402

SAMPLES = [
    dict(name="dark-academia-quote", subject="old library at night, candle, open book", aesthetic="dark-academia",
         template="quote", fmt="ig-post", title="I have always imagined that paradise will be a kind of library.",
         subtitle="Jorge Luis Borges", handle="@pinmuse"),
    dict(name="neon-poster", subject="rainy Tokyo alley with neon signs", aesthetic="cyberpunk-neon", template="poster",
         fmt="pin", title="Neon Nights", subtitle="A field guide to the city after 2am", kicker="Tokyo · Vol. 07",
         handle="@pinmuse", cta="Shibuya → Shinjuku"),
    dict(name="vaporwave-story", subject="retro sunset over a grid horizon", aesthetic="vaporwave", template="story",
         fmt="ig-story", title="Sunset Club", subtitle="Friday • rooftop • 8pm till late",
         kicker="you're invited", cta="RSVP — link in bio", handle="@sunset.club"),
    dict(name="pastel-carousel", subject="dreamy pastel bedroom", aesthetic="pastel-dream", template="carousel",
         fmt="ig-post", title="Make your room feel like a dream", kicker="5 tiny changes",
         handle="@pinmuse", cta="Save this for your next reset",
         slides=[{"title": "Soften the light", "body": "Swap cold bulbs for 2700K and add one lamp at eye level."},
                 {"title": "Pick three colours", "body": "One base, one accent, one surprise. Repeat them everywhere."},
                 {"title": "Add something wavy", "body": "A squiggle mirror or a cloud cushion breaks up straight lines."}]),
    dict(name="coastal-polaroid", subject="striped umbrellas and lemons by the sea", aesthetic="coastal-summer",
         template="polaroid", fmt="ig-post", title="Amalfi", subtitle="the lemon summer, '26",
         kicker="postcards from july", handle="@pinmuse"),
    dict(name="brutalist-swiss", subject="concrete geometry", aesthetic="brutalist", template="swiss",
         fmt="ig-post", title="Form follows feeling", subtitle="An exhibition of raw concrete and hard light.",
         kicker="Exhibit 04 / 2026", handle="@pinmuse"),
    dict(name="old-money-magazine", subject="tennis club, navy blazer, heritage estate", aesthetic="old-money",
         template="magazine", fmt="ig-story", title="Heritage", subtitle="The quiet return of the tennis club",
         kicker="The autumn issue", body="Cable-knit, decoded\nThe new country house\n12 pieces that last",
         handle="@pinmuse"),
    dict(name="gothic-poster", subject="black roses and candelabra", aesthetic="gothic-romance", template="poster",
         fmt="ig-post", title="Midnight Garden", subtitle="Roses, lace and a little bit of ruin.",
         kicker="Limited edition candle", handle="@pinmuse", cta="Shop now"),
    dict(name="boho-minimal", subject="terracotta vases at golden hour", aesthetic="earthy-boho", template="minimal",
         fmt="ig-post", title="Terracotta Hour", subtitle="Handmade ceramics, fired in small batches.",
         kicker="Collection 02", handle="@pinmuse"),
    dict(name="cottage-palette", subject="wildflower meadow", aesthetic="cottagecore", template="palette",
         fmt="pin", title="Meadow", kicker="Palette no. 07", handle="@pinmuse"),
    dict(name="y2k-story", subject="chrome butterfly hair clips, glitter and a pink flip phone, flat lay", aesthetic="y2k", template="story",
         fmt="ig-story", title="Y2K is so back", subtitle="chrome, glitter & flip phones — the drop is live",
         kicker="new drop", cta="Tap to shop", handle="@pinmuse"),
    dict(name="clean-girl-poster", subject="gold hoop earrings and a glass serum bottle on cream linen", aesthetic="clean-girl", template="poster",
         fmt="ig-post", title="Glazed", subtitle="The five-minute morning routine everyone is saving.",
         kicker="Beauty notes", handle="@pinmuse", cta="Read more"),
    dict(name="moody-film-thumb", subject="rainy window, film still", aesthetic="moody-film", template="poster",
         fmt="yt-thumb", title="Films for rainy days", kicker="Watchlist", handle="@pinmuse"),
    dict(name="luxe-collage", subject="travertine and linen still life", aesthetic="minimal-luxe", template="poster",
         fmt="ig-story", title="Quiet Luxury", subtitle="Less, but better.", kicker="The edit", handle="@pinmuse",
         cta="Save"),
    dict(name="matcha-menu", subject="iced matcha latte on a pale oak counter, morning sun, soft shadows", aesthetic="minimal-luxe",
         template="minimal", fmt="ig-post", title="Matcha Mornings", subtitle="Ceremonial grade, whisked to order.",
         kicker="New on the menu", handle="@slowcafe"),
    dict(name="jazz-night", subject="saxophone on a velvet chair in a dim jazz bar, smoke, warm spotlight", aesthetic="moody-film",
         template="poster", fmt="pin", title="Blue Hour Jazz", subtitle="Live quartet every Thursday, 9pm",
         kicker="The Velvet Room", handle="@velvetroom", cta="Free entry before 10"),
    dict(name="ceramics-open-studio", subject="hands shaping clay on a pottery wheel, dusty studio light", aesthetic="earthy-boho",
         template="magazine", fmt="ig-story", title="Open Studio", subtitle="Throw your first bowl with us",
         kicker="Saturday workshop", body="Clay, glaze & tea\nAll levels welcome\nSix seats left", handle="@kilnhouse"),
    dict(name="croissant-launch", subject="a single golden croissant on parchment paper on a marble counter, no people, top light, crumbs", aesthetic="earthy-boho",
         template="poster", fmt="ig-post", title="Butter, Folded 81 Times", subtitle="Our new laminated croissant is here.",
         kicker="Bakery notes", handle="@crumbandco", cta="Order ahead"),
    dict(name="desert-roadtrip", subject="vintage convertible on an empty Arizona desert highway, red rock mesas, golden hour", aesthetic="earthy-boho",
         template="polaroid", fmt="ig-post", title="Route 66", subtitle="nine days, no plans",
         kicker="road trip diaries", handle="@pinmuse"),
    dict(name="record-store", subject="stacks of vinyl records in a sunlit record store, orange and cream", aesthetic="brutalist",
         template="swiss", fmt="ig-post", title="Record Store Day", subtitle="Rare pressings, live DJs, cheap coffee.",
         kicker="April 18 / 2026", handle="@spinshop"),
    dict(name="book-club-story", subject="stack of old leather books and a teacup by a rainy window, candlelight", aesthetic="dark-academia",
         template="story", fmt="ig-story", title="Book Club", subtitle="This month: The Secret History",
         kicker="you're invited", cta="Join the list", handle="@readingroom"),
    dict(name="autumn-recipe", subject="rustic apple tart on a linen cloth with autumn leaves, overhead", aesthetic="cottagecore",
         template="poster", fmt="pin", title="Apple Tart", subtitle="A weekend bake with five ingredients",
         kicker="Autumn kitchen", handle="@pinmuse", cta="Recipe inside"),
    dict(name="ski-chalet", subject="snowy alpine chalet at dusk with warm windows, pine trees", aesthetic="old-money",
         template="magazine", fmt="ig-story", title="Après", subtitle="The winter escape issue",
         kicker="Season 26/27", body="Five chalets worth the drive\nThe cashmere edit\nFondue, properly", handle="@pinmuse"),
    dict(name="perfume-launch", subject="amber glass perfume bottle on travertine with dried roses, soft shadow", aesthetic="minimal-luxe",
         template="minimal", fmt="pin", title="Ambre Nuit", subtitle="Eau de parfum. Warm, slow, close to skin.",
         kicker="Fall 2026", handle="@maisonambre"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="procedural")
    ap.add_argument("--inspo", action="store_true", help="research Pinterest for each sample (needs network)")
    ap.add_argument("--out", default=str(ROOT / "examples" / "gallery"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "_runs"
    for s in SAMPLES:
        s = dict(s)
        name = s.pop("name")
        m = create(s.pop("subject"), provider=a.provider, out_dir=str(tmp),
                   inspo=(s["aesthetic"].replace("-", " ") + " aesthetic") if a.inspo else None, seed=7, **s)
        for i, f in enumerate(m["outputs"]):
            suffix = f"-{i + 1}" if len(m["outputs"]) > 1 else ""
            shutil.copy(f, out / f"{name}{suffix}.jpg")
        print(name, "→", len(m["outputs"]), "file(s)", m["provider"])
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
