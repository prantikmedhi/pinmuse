from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Pin:
    """One piece of inspiration, normalised across every source backend."""

    id: str
    image_url: str
    title: str = ""
    description: str = ""
    link: str = ""  # outbound link the pin points to
    url: str = ""  # the pin page itself
    width: int = 0
    height: int = 0
    dominant_color: str = ""
    saves: int = 0
    board: str = ""
    pinner: str = ""
    source: str = "web"  # which backend produced it
    local_path: str = ""  # filled once the image is cached
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return " ".join(x for x in (self.title, self.description, self.board) if x).strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Pin":
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        return cls(**known)


@dataclass
class Moodboard:
    """What the agent learned from a set of pins: the visual direction for new work."""

    query: str
    pins: list[Pin]
    palette: list[str]  # hex colours, most dominant first
    palette_weights: list[float]
    brightness: float  # 0..1
    contrast: float  # 0..1
    saturation: float  # 0..1
    warmth: float  # -1 (cool) .. 1 (warm)
    keywords: list[str]
    aesthetic: str  # best-matching aesthetic preset name
    aesthetic_scores: dict[str, float]
    orientation: str  # portrait / square / landscape majority
    descriptors: list[str]  # human words: "airy", "moody", "high-contrast" ...
    contact_sheet: str = ""  # path to the moodboard collage image

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pins"] = [p.to_dict() for p in self.pins]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Moodboard":
        d = dict(d)
        d["pins"] = [Pin.from_dict(p) for p in d.get("pins", [])]
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        return cls(**known)
