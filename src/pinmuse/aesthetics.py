"""A library of Pinterest-native aesthetics.

Each preset tells the generator how to *prompt*, and the composer how to *typeset*.
Analysis scores a moodboard against every preset so the agent gets a named direction
("dark academia, 0.71") instead of a vague vibe.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Aesthetic:
    name: str
    keywords: tuple[str, ...]
    palette: tuple[str, ...]
    style: str  # prompt fragment
    lighting: str
    camera: str
    fonts: tuple[str, str]  # (display, body)
    effects: tuple[str, ...] = ()
    templates: tuple[str, ...] = ("poster",)
    negative: str = "text, watermark, logo, signature, extra fingers, deformed, low quality, jpeg artifacts"
    target: dict = field(default_factory=dict)  # brightness/saturation/warmth targets for scoring


A = Aesthetic
PRESETS: dict[str, Aesthetic] = {a.name: a for a in [
    A("minimal-luxe", ("minimal", "luxury", "neutral", "beige", "clean", "aesthetic", "home", "elegant"),
      ("#F3EEE7", "#D9CBB8", "#A68A6D", "#5C4A3A", "#1E1B18"),
      "quiet luxury, minimalist editorial still life, travertine and linen textures, negative space",
      "soft diffused window light, long gentle shadows", "50mm, f/2.8, eye level",
      ("Italiana", "Inter"), ("grain",), ("minimal", "poster", "magazine"),
      target={"brightness": .75, "saturation": .18, "warmth": .4}),
    A("dark-academia", ("academia", "books", "library", "vintage", "classic", "poetry", "autumn", "study"),
      ("#2B2118", "#4A3426", "#7A5C3E", "#B59368", "#E6D5B8"),
      "dark academia, old library, leather-bound books, candlelight, oil-painting mood, tweed and brass",
      "low-key chiaroscuro, warm candle glow", "35mm film, shallow depth of field",
      ("PlayfairDisplay", "CormorantGaramond-Italic"), ("grain", "vignette"), ("quote", "poster", "polaroid"),
      target={"brightness": .28, "saturation": .35, "warmth": .6}),
    A("clean-girl", ("clean", "girl", "glow", "skincare", "slick", "gold", "hoops", "latte", "glazed"),
      ("#FBF6F1", "#EAD8C8", "#D6B49A", "#B98B6E", "#FFFFFF"),
      "clean girl aesthetic, glazed skin glow, slicked-back bun, gold hoops, latte tones, soft beauty editorial",
      "bright soft beauty light, clean highlights", "85mm portrait, f/1.8",
      ("DMSerifDisplay", "Inter"), ("grain",), ("story", "minimal", "magazine"),
      target={"brightness": .82, "saturation": .22, "warmth": .5}),
    A("y2k", ("y2k", "2000s", "chrome", "butterfly", "glitter", "pink", "cyber", "pop", "bratz"),
      ("#FF5FCB", "#B6F0FF", "#C9C9D6", "#7B2FFF", "#FFF35C"),
      "Y2K aesthetic, chrome liquid metal, iridescent holographic gradients, butterfly clips, glossy pop",
      "high-key flash photography, glossy specular highlights", "wide angle, flash, slight fisheye",
      ("ArchivoBlack", "SpaceGrotesk"), ("grain",), ("swiss", "story", "poster"),
      target={"brightness": .7, "saturation": .8, "warmth": 0}),
    A("cottagecore", ("cottage", "cottagecore", "floral", "garden", "picnic", "meadow", "bread", "linen", "vintage"),
      ("#F4EBDD", "#CFD8B6", "#8FA67E", "#D99A8B", "#6B4F3A"),
      "cottagecore, wildflower meadow, gingham picnic, sourdough and jam, soft pastoral romance",
      "golden-hour backlight, hazy and dreamy", "35mm film, Portra 400 tones",
      ("CormorantGaramond-Italic", "Inter"), ("grain", "lightleak"), ("polaroid", "quote", "poster"),
      target={"brightness": .7, "saturation": .35, "warmth": .55}),
    A("cyberpunk-neon", ("neon", "cyberpunk", "night", "city", "tokyo", "rain", "synthwave", "futuristic"),
      ("#0B0B1A", "#1E1145", "#FF2E88", "#00F0FF", "#F9F871"),
      "cyberpunk neon cityscape, rain-slick streets, holographic signage, magenta and cyan glow",
      "neon rim light, volumetric haze, reflections", "anamorphic 35mm, cinematic",
      ("BebasNeue", "SpaceGrotesk"), ("grain", "vignette"), ("poster", "swiss", "story"),
      target={"brightness": .22, "saturation": .85, "warmth": -.3}),
    A("coastal-summer", ("beach", "summer", "coastal", "ocean", "mediterranean", "sea", "italy", "travel"),
      ("#F6F1E7", "#9CCBD6", "#2C7DA0", "#E9C46A", "#F4A261"),
      "coastal Mediterranean summer, whitewashed walls, cobalt sea, lemons and striped umbrellas",
      "high noon sun, crisp shadows, sun-bleached", "35mm film, slightly overexposed",
      ("DMSerifDisplay", "Inter"), ("grain", "lightleak"), ("poster", "polaroid", "story"),
      target={"brightness": .72, "saturation": .5, "warmth": .25}),
    A("brutalist", ("brutalist", "concrete", "architecture", "graphic", "bold", "grid", "swiss", "type"),
      ("#EDEDED", "#BDBDBD", "#111111", "#FF3B00", "#2B2B2B"),
      "brutalist architecture, raw concrete forms, stark geometry, Swiss graphic design energy",
      "hard directional sunlight, deep shadows", "wide architectural lens, symmetrical",
      ("ArchivoBlack", "SpaceGrotesk"), ("grain",), ("swiss", "poster"),
      target={"brightness": .55, "saturation": .12, "warmth": 0}),
    A("old-money", ("old money", "money", "ralph", "equestrian", "tennis", "yacht", "preppy", "classic"),
      ("#F2EFE6", "#1F3A2E", "#7B6A4F", "#C8B28A", "#0E1A2B"),
      "old money aesthetic, equestrian estate, cable-knit and navy blazers, tennis club, understated heritage",
      "soft overcast daylight, timeless", "medium format film, Kodak Gold",
      ("PlayfairDisplay", "Inter"), ("grain",), ("magazine", "minimal", "poster"),
      target={"brightness": .5, "saturation": .25, "warmth": .3}),
    A("vaporwave", ("vaporwave", "retro", "80s", "90s", "sunset", "palm", "grid", "statue", "aesthetic"),
      ("#2D0B59", "#FF6AD5", "#C774E8", "#94D0FF", "#FFD3A5"),
      "vaporwave, pastel sunset gradient, greek statue bust, palm silhouettes, retro grid horizon",
      "dreamy gradient sky glow", "flat frontal composition",
      ("Syne", "SpaceGrotesk"), ("grain", "scanlines"), ("poster", "story"),
      target={"brightness": .5, "saturation": .7, "warmth": .1}),
    A("moody-film", ("moody", "film", "35mm", "analog", "cinematic", "rain", "nostalgia", "grain", "photography"),
      ("#1B1D1E", "#3D4A4F", "#7D8C84", "#C4B69A", "#E8E1D3"),
      "moody analog film still, cinematic melancholy, muted teal and cream, quiet storytelling",
      "overcast or blue-hour light, soft contrast", "35mm film, Cinestill 800T, halation",
      ("PlayfairDisplay-Italic", "Inter"), ("grain", "vignette", "lightleak"), ("minimal", "polaroid", "story"),
      target={"brightness": .35, "saturation": .25, "warmth": -.1}),
    A("pastel-dream", ("pastel", "kawaii", "soft", "dreamy", "cute", "cloud", "danish", "pastel aesthetic"),
      ("#FDE2E4", "#E2ECE9", "#CDDAFD", "#FFF1C1", "#BEE1E6"),
      "danish pastel, soft dreamy interiors, cloud shapes, wavy mirrors, checkerboard and tulips",
      "airy high-key light, no harsh shadows", "flat lay or straight-on, clean",
      ("Syne", "Inter"), (), ("story", "swiss", "quote"),
      target={"brightness": .88, "saturation": .3, "warmth": .1}),
    A("earthy-boho", ("boho", "earthy", "terracotta", "macrame", "desert", "plants", "rattan", "natural"),
      ("#E9DCC9", "#C97B4A", "#9C5A3C", "#6E7F5C", "#3F3428"),
      "earthy boho, terracotta and rattan, desert plants, handmade ceramics, sun-dappled linen",
      "warm late-afternoon light through leaves", "35mm, natural",
      ("DMSerifDisplay", "Inter"), ("grain",), ("polaroid", "poster", "minimal"),
      target={"brightness": .55, "saturation": .4, "warmth": .7}),
    A("gothic-romance", ("gothic", "goth", "dark", "romantic", "roses", "victorian", "witchy", "lace"),
      ("#0E0B0F", "#2E1A24", "#5B1A2E", "#9E2B4A", "#D9C3B0"),
      "gothic romance, black roses and lace, candelabras, velvet, Victorian melancholy",
      "candlelight, deep shadows, crimson accents", "50mm, low-key",
      ("PlayfairDisplay-Italic", "CormorantGaramond-Italic"), ("grain", "vignette"), ("quote", "poster"),
      target={"brightness": .18, "saturation": .45, "warmth": .2}),
]}

DEFAULT = "minimal-luxe"


def get(name: str | None) -> Aesthetic:
    if not name:
        return PRESETS[DEFAULT]
    key = name.lower().replace(" ", "-")
    if key in PRESETS:
        return PRESETS[key]
    for k in PRESETS:
        if key in k or k in key:
            return PRESETS[k]
    raise KeyError(f"unknown aesthetic {name!r}. Options: {', '.join(PRESETS)}")
