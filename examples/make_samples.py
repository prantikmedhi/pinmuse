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
    dict(name="croissant-launch", subject="a single golden croissant on parchment paper on a marble counter, no people, top light, crumbs", aesthetic="earthy-boho",
         template="poster", fmt="ig-post", title="Butter, Folded 81 Times", subtitle="Our new laminated croissant is here.",
         kicker="Bakery notes", handle="@crumbandco", cta="Order ahead"),
    dict(name="desert-roadtrip", subject="vintage convertible on an empty Arizona desert highway, red rock mesas, golden hour", aesthetic="earthy-boho",
         template="polaroid", fmt="ig-post", title="Route 66", subtitle="nine days, no plans",
         kicker="road trip diaries", handle="@pinmuse"),
    dict(name="record-store", subject="stacks of vinyl records in a sunlit record store, orange and cream", aesthetic="brutalist",
         template="swiss", fmt="ig-post", title="Record Store Day", subtitle="Rare pressings, live DJs, cheap coffee.",
         kicker="April 18 / 2026", handle="@spinshop"),
    dict(name="autumn-recipe", subject="rustic apple tart on a linen cloth with autumn leaves, overhead", aesthetic="cottagecore",
         template="poster", fmt="pin", title="Apple Tart", subtitle="A weekend bake with five ingredients",
         kicker="Autumn kitchen", handle="@pinmuse", cta="Recipe inside"),
    dict(name="ski-chalet", subject="snowy alpine chalet at dusk with warm windows, pine trees", aesthetic="old-money",
         template="magazine", fmt="ig-story", title="Après", subtitle="The winter escape issue",
         kicker="Season 26/27", body="Five chalets worth the drive\nThe cashmere edit\nFondue, properly", handle="@pinmuse"),
    dict(name="perfume-launch", subject="amber glass perfume bottle on travertine with dried roses, soft shadow", aesthetic="minimal-luxe",
         template="minimal", fmt="pin", title="Ambre Nuit", subtitle="Eau de parfum. Warm, slow, close to skin.",
         kicker="Fall 2026", handle="@maisonambre"),
    # carousels: every slide gets its own generated photo (slide "subject")
    dict(name="unreal-places", subject="salt flat mirror reflecting a pink sunset sky, lone figure, endless horizon",
         aesthetic="moody-film", template="carousel", fmt="ig-post", title="Places that look unreal",
         kicker="Save for your next trip", handle="@pinmuse", cta="Which one is first on your list?",
         slides=[{"title": "Zhangjiajie, China", "body": "Sandstone pillars in the fog. Go at dawn, before the cable cars.",
                  "subject": "towering sandstone pillars rising from thick fog at dawn, Zhangjiajie, aerial"},
                 {"title": "Vaadhoo, Maldives", "body": "The shoreline glows blue on warm nights. New moon is best.",
                  "subject": "bioluminescent waves glowing electric blue on a dark beach at night, long exposure stars"},
                 {"title": "Cappadocia, Turkey", "body": "Hundreds of balloons over fairy chimneys at sunrise.",
                  "subject": "hundreds of hot air balloons over fairy chimney rock valleys at sunrise, golden haze"},
                 {"title": "Lofoten, Norway", "body": "Red cabins, black peaks, and the aurora overhead.",
                  "subject": "green aurora borealis over jagged black peaks and red fishing cabins reflected in a fjord"}]),
    dict(name="neon-photo-tips", subject="rain soaked neon street at night reflected in puddles, cinematic, lone umbrella",
         aesthetic="cyberpunk-neon", template="carousel", fmt="ig-post", title="Shoot the city at night",
         kicker="4 photo tricks", handle="@pinmuse", cta="Try one tonight and tag us",
         slides=[{"title": "Find the puddles", "body": "Get low after rain. Every sign doubles in the reflection.",
                  "subject": "macro low angle of a puddle reflecting pink and cyan neon signs, raindrops rippling"},
                 {"title": "Drag the shutter", "body": "Two seconds on a tripod turns traffic into ribbons of light.",
                  "subject": "long exposure light trails of traffic through a neon lit intersection from above"},
                 {"title": "Shoot through glass", "body": "Rainy windows blur the city into colour. Focus on the drops.",
                  "subject": "raindrops on a window with a blurry neon city bokeh behind, shallow depth of field"},
                 {"title": "Wait for a silhouette", "body": "One figure under a sign gives the frame a story.",
                  "subject": "silhouette of a person with a clear umbrella under a giant glowing red neon sign"}]),
    dict(name="coffee-guide", subject="pour over coffee being brewed, steam curling in a beam of morning light, dark background",
         aesthetic="earthy-boho", template="carousel", fmt="ig-post", title="Better coffee at home",
         kicker="The slow guide", handle="@slowcafe", cta="Save this for tomorrow morning",
         slides=[{"title": "Grind fresh", "body": "Grind right before brewing. Medium-fine for pour-over, like sea salt.",
                  "subject": "extreme macro of freshly ground coffee falling from a burr grinder, dramatic side light"},
                 {"title": "Mind the water", "body": "93°C, just off the boil. Bloom with twice the coffee's weight.",
                  "subject": "slow motion splash of hot water hitting coffee grounds, blooming bubbles, steam, macro"},
                 {"title": "Pull it short", "body": "A good espresso has tiger-striped crema and takes about 28 seconds.",
                  "subject": "espresso pouring from a bottomless portafilter, thick golden crema, macro, dark moody"}]),
    dict(name="brutalist-guide", subject="massive brutalist concrete tower against a clear blue sky, low angle, hard shadows",
         aesthetic="brutalist", template="carousel", fmt="ig-post", title="Concrete, but make it beautiful",
         kicker="Brutalism 101", handle="@pinmuse", cta="Follow for more architecture",
         slides=[{"title": "The Barbican, London", "body": "Towers, lakes and walkways. A city inside a building.",
                  "subject": "brutalist concrete towers with balconies full of hanging plants over a still lake"},
                 {"title": "Habitat 67, Montreal", "body": "354 stacked boxes, each with its own garden.",
                  "subject": "stacked brutalist concrete cubes forming a hillside of apartments, geometric, sunlight"},
                 {"title": "Spiral stairs", "body": "Look up. Brutalism hides its best shapes in stairwells.",
                  "subject": "looking straight up a raw concrete spiral staircase, perfect geometry, dramatic light"}]),
    dict(name="y2k-drop", subject="chrome liquid metal sneaker floating in a pink holographic void, studio product shot",
         aesthetic="y2k", template="carousel", fmt="ig-post", title="The chrome drop",
         kicker="New collection", handle="@pinmuse", cta="Shop the drop, link in bio",
         slides=[{"title": "Liquid metal bag", "body": "Mirror finish, butterfly clasp, fits a flip phone and a lip gloss.",
                  "subject": "mirror chrome handbag with a butterfly clasp floating over iridescent glitter, product shot"},
                 {"title": "Holo shades", "body": "Wraparound lenses that throw rainbows on everything.",
                  "subject": "wraparound holographic sunglasses refracting rainbow light on a lavender background"},
                 {"title": "Glitter platforms", "body": "Five inches of sparkle. Surprisingly walkable.",
                  "subject": "glitter platform boots on a reflective chrome floor, pink and blue rim light"}]),
    # bold single posters
    dict(name="moon-desert", subject="a giant full moon rising behind a lone figure on a red desert dune, surreal scale",
         aesthetic="moody-film", template="poster", fmt="pin", title="Far Away", subtitle="A film about leaving everything behind",
         kicker="In cinemas soon", handle="@pinmuse", cta="Watch the trailer"),
    dict(name="jellyfish-story", subject="glowing jellyfish drifting in deep dark ocean water, bioluminescent, cinematic",
         aesthetic="cyberpunk-neon", template="story", fmt="ig-story", title="Deep Glow", subtitle="The aquarium after dark • Fridays",
         kicker="new exhibit", cta="Book tickets", handle="@oceanhall"),
    dict(name="flower-burst", subject="an explosion of fresh flower petals frozen mid air against a deep green background",
         aesthetic="cottagecore", template="minimal", fmt="ig-post", title="Bloom Season", subtitle="Fresh cut flowers, delivered Fridays.",
         kicker="Spring 2027", handle="@petalpost"),
    dict(name="iceland-swiss", subject="a lone red cabin under a towering black volcanic mountain, dramatic storm clouds",
         aesthetic="brutalist", template="swiss", fmt="ig-post", title="Iceland in Winter",
         subtitle="Ten days, one road, no signal.", kicker="Travel journal 03", handle="@pinmuse"),
    # product-surreal carousels in the spirit of "The chrome drop", each in a different look
    dict(name="glass-objects", subject="headphones made of clear iridescent glass floating over a soft aqua gradient, hyper-real studio product photography, no people",
         aesthetic="minimal-luxe", template="carousel", fmt="ig-post", title="Made of glass",
         kicker="Object study 01", handle="@pinmuse", cta="Save the one you'd break first",
         slides=[{"title": "Glass headphones", "body": "Clear, iridescent, and absolutely impractical.",
                  "subject": "transparent glass over-ear headphones refracting rainbow caustics on white stone, hyper-real studio product photography, no people"},
                 {"title": "Glass sneaker", "body": "A trainer you would never wear outside.",
                  "subject": "a sneaker sculpted from frosted glass with light caustics on a pale blue floor, hyper-real studio product photography, no people"},
                 {"title": "Glass camera", "body": "Every gear visible. Every shot a little blurry.",
                  "subject": "a retro film camera made of clear glass with visible internal parts, soft studio light, hyper-real studio product photography, no people"}]),
    dict(name="jelly-tech", subject="a translucent strawberry jelly game controller wobbling on a pink pedestal, hyper-real studio product photography, no people",
         aesthetic="pastel-dream", template="carousel", fmt="ig-post", title="Soft tech",
         kicker="The jelly collection", handle="@pinmuse", cta="Which one would you squish?",
         slides=[{"title": "Gummy keyboard", "body": "Every key a little gummy bear. Typing feels like snacking.",
                  "subject": "a mechanical keyboard with translucent gummy candy keycaps in pastel colours, macro, hyper-real studio product photography, no people"},
                 {"title": "Jelly speaker", "body": "The bass makes it wobble. That's the feature.",
                  "subject": "a translucent lime jelly bluetooth speaker wobbling, glossy, pastel background, hyper-real studio product photography, no people"},
                 {"title": "Candy phone", "body": "A flip phone cast in boiled sweets.",
                  "subject": "a flip phone made of translucent hard candy in cherry red and lemon, sparkling sugar, hyper-real studio product photography, no people"}]),
    dict(name="citrus-acid", subject="an aluminium soda can bursting through a wall of sliced oranges and lime, splash frozen mid air, hyper-real studio product photography, no people",
         aesthetic="brutalist", template="carousel", fmt="ig-post", title="Squeeze the day",
         kicker="Summer drop", handle="@pinmuse", cta="Pick your flavour",
         slides=[{"title": "Blood orange", "body": "Bitter, bright, and a little dramatic.",
                  "subject": "a blood orange sliced in half with juice exploding in a perfect crown splash, hard flash, hyper-real studio product photography, no people"},
                 {"title": "Electric lime", "body": "Sharp enough to wake up the whole street.",
                  "subject": "neon green limes and ice cubes falling through fizzing soda bubbles, hard flash, black background, hyper-real studio product photography, no people"},
                 {"title": "Yuzu", "body": "Floral, sour, and impossible to find.",
                  "subject": "a single yuzu on a stack of yellow geometric blocks, harsh sunlight, long shadow, hyper-real studio product photography, no people"}]),
    dict(name="inflatable", subject="a giant glossy inflatable puffer handbag in cobalt blue on a white cyclorama, hyper-real studio product photography, no people",
         aesthetic="coastal-summer", template="carousel", fmt="ig-post", title="Everything is inflatable",
         kicker="Puff season", handle="@pinmuse", cta="Save for your next impulse buy",
         slides=[{"title": "Puffer chair", "body": "Sit down slowly. Then bounce.",
                  "subject": "a glossy inflatable armchair in bubblegum pink, studio, soft shadow, hyper-real studio product photography, no people"},
                 {"title": "Balloon heels", "body": "Shoes that float a little off the ground.",
                  "subject": "high heels made of twisted glossy balloons in orange, floating, pale lilac background, hyper-real studio product photography, no people"},
                 {"title": "Air headphones", "body": "Pillowy, puffy, and very loud.",
                  "subject": "puffy inflatable headphones in mint green vinyl, glossy highlights, studio, hyper-real studio product photography, no people"}]),
    dict(name="space-age", subject="a chrome retro rocket shaped toaster with toast popping out, floating among planets, hyper-real studio product photography, no people",
         aesthetic="vaporwave", template="carousel", fmt="ig-post", title="Space age kitchen",
         kicker="Retro futures", handle="@pinmuse", cta="Tag someone who needs a rocket toaster",
         slides=[{"title": "Orbit kettle", "body": "It whistles like a launch countdown.",
                  "subject": "a domed chrome kettle with tiny rocket fins on a purple sunset moonscape, hyper-real studio product photography, no people"},
                 {"title": "Moon boot mixer", "body": "Stand mixer, but make it lunar.",
                  "subject": "a pastel stand mixer shaped like a moon boot on a crater surface, stars, earthrise, hyper-real studio product photography, no people"},
                 {"title": "Saturn lamp", "body": "Ring included. Gravity not.",
                  "subject": "a glowing orange Saturn shaped lamp with a chrome ring hovering in a dark retro room, hyper-real studio product photography, no people"}]),
    dict(name="noir-edit", subject="a matte black wristwatch on black volcanic rock lit by a single thin beam of gold light, hyper-real studio product photography, no people",
         aesthetic="gothic-romance", template="carousel", fmt="ig-post", title="The noir edit",
         kicker="Black on black", handle="@pinmuse", cta="Save the darkest one",
         slides=[{"title": "Obsidian ring", "body": "Polished stone, sharp edges, no shine except yours.",
                  "subject": "an obsidian ring on black velvet with a single rim light, extreme macro, hyper-real studio product photography, no people"},
                 {"title": "Matte perfume", "body": "A bottle that eats the light.",
                  "subject": "a matte black faceted perfume bottle on wet black slate, smoke curling, thin gold light, hyper-real studio product photography, no people"},
                 {"title": "Ink sneaker", "body": "Triple black, dipped in ink.",
                  "subject": "a black sneaker half dipped into glossy black ink, droplets frozen, dark studio, hyper-real studio product photography, no people"}]),
    dict(name="clay-world", subject="a cute matte clay sculpted vintage camera in sage and peach, soft daylight, tiny fingerprints, hyper-real studio product photography, no people",
         aesthetic="cottagecore", template="carousel", fmt="ig-post", title="Made of clay",
         kicker="Handmade gadgets", handle="@pinmuse", cta="Follow for more tiny things",
         slides=[{"title": "Clay radio", "body": "Lumpy, warm, and it really plays.",
                  "subject": "a chunky matte clay retro radio in butter yellow with sculpted knobs on linen, hyper-real studio product photography, no people"},
                 {"title": "Clay sneakers", "body": "Pressed by hand, one thumbprint at a time.",
                  "subject": "a pair of sneakers sculpted from soft terracotta and cream clay, soft daylight, hyper-real studio product photography, no people"},
                 {"title": "Clay console", "body": "A handheld game console that fits in a palm of clay.",
                  "subject": "a handheld game console sculpted from pastel clay with tiny buttons, soft shadow, hyper-real studio product photography, no people"}]),
    # posters / stories in the same spirit
    dict(name="fizz-story", subject="a soda can exploding into a fountain of pink fizz and ice under neon light, hyper-real studio product photography, no people",
         aesthetic="cyberpunk-neon", template="story", fmt="ig-story", title="FIZZ", subtitle="Cherry cola, zero sugar • out now",
         kicker="new flavour", cta="Find a store", handle="@fizzco"),
    dict(name="melting-chrome", subject="a chrome ice cream cone melting into liquid mirror metal on a red floor, hyper-real studio product photography, no people",
         aesthetic="brutalist", template="swiss", fmt="ig-post", title="Hot Metal Summer",
         subtitle="A chrome dessert pop-up, three days only.", kicker="Pop-up 07 / 2027", handle="@pinmuse"),
    dict(name="fruit-sculpture", subject="a floating sculpture of sliced fruit arranged in a perfect sphere, pastel sky, hyper-real studio product photography, no people",
         aesthetic="minimal-luxe", template="minimal", fmt="pin", title="Still Life, Moving",
         subtitle="A fruit sculpture series in twelve parts.", kicker="Exhibit", handle="@pinmuse"),
    dict(name="glass-koi", subject="glass koi fish swimming through a pool of liquid gold, top down, hyper-real studio product photography, no people",
         aesthetic="old-money", template="magazine", fmt="ig-story", title="Gilded",
         subtitle="The glass issue", kicker="Vol. 12", body="Blown, cast & poured\nGold leaf, again\nThe koi pond studio",
         handle="@pinmuse"),
    dict(name="levitating-sneaker", subject="a holographic sneaker levitating above a neon pink floor with scattered light, hyper-real studio product photography, no people",
         aesthetic="y2k", template="poster", fmt="pin", title="Zero Gravity", subtitle="The levitation runner. Drops Friday.",
         kicker="Release 04", handle="@pinmuse", cta="Set a reminder"),
    dict(name="flower-computer", subject="wildflowers and moss growing out of a beige retro computer in a sunlit field, hyper-real studio product photography, no people",
         aesthetic="earthy-boho", template="poster", fmt="ig-post", title="Grow Offline",
         subtitle="A weekend without screens, mostly.", kicker="Retreat notes", handle="@pinmuse", cta="Join the waitlist"),
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
