from __future__ import annotations

import base64
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GenRequest:
    prompt: str
    out: Path
    negative: str = ""
    width: int = 1024
    height: int = 1536
    refs: list[str] = field(default_factory=list)  # local image paths used as style references
    seed: int | None = None
    palette: list[str] = field(default_factory=list)  # used by the procedural provider
    aesthetic: str = ""

    @property
    def size(self) -> str:
        """Nearest of the three sizes most hosted models accept."""
        r = self.height / self.width
        return "1024x1536" if r > 1.15 else "1536x1024" if r < 0.87 else "1024x1024"

    @property
    def aspect(self) -> str:
        options = {"1:1": 1, "2:3": 1.5, "3:2": 2 / 3, "3:4": 4 / 3, "4:3": .75, "4:5": 1.25, "5:4": .8,
                   "9:16": 16 / 9, "16:9": 9 / 16, "21:9": 9 / 21}
        r = self.height / self.width
        return min(options, key=lambda k: abs(options[k] - r))


class Provider:
    name = "base"
    kind = "cloud"
    setup = ""
    supports_refs = False

    def available(self) -> bool:
        raise NotImplementedError

    def generate(self, req: GenRequest) -> Path:
        raise NotImplementedError

    @staticmethod
    def save_b64(b64: str, out: Path) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(b64))
        return out

    @staticmethod
    def save_bytes(data: bytes, out: Path) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        return out
