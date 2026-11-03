"""Write the image-model prompt from what was learned on Pinterest."""

from __future__ import annotations

from . import aesthetics
from .formats import Format
from .models import Moodboard

# Where the composer will put type, so the image leaves room for it.
SPACE_FOR_TEXT = {
    "poster": "clear negative space in the upper third for a headline",
    "magazine": "subject centred and slightly low, empty sky/background at the top for a masthead",
    "story": "subject in the middle band, calm uncluttered top and bottom areas",
    "quote": "soft abstract background texture, no focal subject, lots of empty space",
    "minimal": "single subject, generous empty margins",
    "polaroid": "candid snapshot composition",
    "swiss": "bold graphic subject on one side, flat empty area on the other",
    "carousel": "clean background with room for text",
    "palette": "abstract colour study",
    "collage": "",
}


def build(subject: str, mb: Moodboard | None = None, aesthetic: str | None = None,
          fmt: Format | None = None, template: str = "poster", extra: str = "") -> dict[str, str]:
    a = aesthetics.get(aesthetic or (mb.aesthetic if mb else None))
    parts = [subject.strip().rstrip(".")]
    parts.append(a.style)
    if mb:
        if mb.palette:
            parts.append("colour palette " + ", ".join(mb.palette[:5]))
        parts.append(", ".join(mb.descriptors))
        motif = [k for k in mb.keywords if k not in subject.lower()][:6]
        if motif:
            parts.append("motifs: " + ", ".join(motif))
    else:
        parts.append("colour palette " + ", ".join(a.palette))
    parts += [a.lighting, a.camera]
    if SPACE_FOR_TEXT.get(template):
        parts.append(SPACE_FOR_TEXT[template])
    if fmt:
        parts.append(f"{fmt.aspect} composition")
    parts.append("Pinterest-worthy, editorial, highly aesthetic, cohesive styling, no text or lettering in the image")
    if extra:
        parts.append(extra)
    return {"prompt": ". ".join(p for p in parts if p) + ".", "negative": a.negative, "aesthetic": a.name}
