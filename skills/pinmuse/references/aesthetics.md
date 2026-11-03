# Aesthetic presets

`analyze` scores every moodboard against these presets (keywords 45%, palette distance 30%,
brightness/saturation/warmth 25%). Treat the top score as a starting point. Override it with
`--aesthetic` when you can see on the contact sheet that something else fits better.

| Preset | Reach for it when… | Display / body font | Best templates |
|---|---|---|---|
| `minimal-luxe` | home, wellness, skincare, "quiet luxury", neutral interiors | Italiana / Inter | minimal, poster, magazine |
| `dark-academia` | books, study, poetry, autumn, classical music | Playfair / Cormorant Italic | quote, poster, polaroid |
| `clean-girl` | beauty, morning routines, latte tones, glow | DM Serif / Inter | story, minimal, magazine |
| `y2k` | fashion drops, Gen-Z, chrome, glitter, pop | Archivo Black / Space Grotesk | swiss, story, poster |
| `cottagecore` | baking, gardens, picnics, florals, slow living | Cormorant Italic / Inter | polaroid, quote, poster |
| `cyberpunk-neon` | nightlife, gaming, tech, music events | Bebas Neue / Space Grotesk | poster, swiss, story |
| `coastal-summer` | travel, summer menus, Mediterranean | DM Serif / Inter | poster, polaroid, story |
| `brutalist` | architecture, design studios, exhibitions | Archivo Black / Space Grotesk | swiss, poster |
| `old-money` | heritage brands, menswear, tennis, equestrian | Playfair / Inter | magazine, minimal, poster |
| `vaporwave` | retro parties, synth music, nostalgia | Syne / Space Grotesk | poster, story |
| `moody-film` | photography, film lists, melancholy, rain | Playfair Italic / Inter | minimal, polaroid, story |
| `pastel-dream` | kids, rooms, cute products, tips carousels | Syne / Inter | story, swiss, quote, carousel |
| `earthy-boho` | ceramics, plants, handmade goods, desert | DM Serif / Inter | polaroid, poster, minimal |
| `gothic-romance` | candles, Halloween, dark florals, romance books | Playfair Italic / Cormorant Italic | quote, poster |

A brand kit (`--brand brand.json`) overrides palette and fonts:

```json
{"handle": "@studio", "palette": ["#F4EFE6", "#1F3A2E", "#C8B28A"], "display_font": "PlayfairDisplay",
 "body_font": "Inter", "logo": "logo.png"}
```

Bundled fonts (all SIL OFL): PlayfairDisplay(-Italic), DMSerifDisplay(-Italic), Italiana,
CormorantGaramond-Italic, Caveat, Inter, SpaceGrotesk, BebasNeue, ArchivoBlack, Syne. Any `.ttf`
path also works.
