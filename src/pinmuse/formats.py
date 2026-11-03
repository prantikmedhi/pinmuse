"""Canvas sizes and safe zones for every place a post ends up."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Format:
    name: str
    width: int
    height: int
    label: str
    safe_top: float = 0.0  # fraction of height covered by platform UI
    safe_bottom: float = 0.0
    gen_size: str = "1024x1536"  # nearest size most image models accept

    @property
    def aspect(self) -> str:
        from math import gcd
        g = gcd(self.width, self.height)
        return f"{self.width // g}:{self.height // g}"


F = Format
FORMATS: dict[str, Format] = {f.name: f for f in [
    F("ig-post", 1080, 1350, "Instagram feed post (4:5)", gen_size="1024x1536"),
    F("ig-square", 1080, 1080, "Instagram square (1:1)", gen_size="1024x1024"),
    F("ig-story", 1080, 1920, "Instagram / Facebook story (9:16)", .12, .18, "1024x1536"),
    F("reel-cover", 1080, 1920, "Reel / TikTok / Shorts cover (9:16)", .10, .22, "1024x1536"),
    F("pin", 1000, 1500, "Pinterest standard pin (2:3)", gen_size="1024x1536"),
    F("pin-long", 1000, 2100, "Pinterest long pin (1:2.1)", gen_size="1024x1536"),
    F("x-post", 1600, 900, "X / Twitter in-feed (16:9)", gen_size="1536x1024"),
    F("linkedin", 1200, 1200, "LinkedIn square", gen_size="1024x1024"),
    F("linkedin-wide", 1200, 627, "LinkedIn link share (1.91:1)", gen_size="1536x1024"),
    F("yt-thumb", 1280, 720, "YouTube thumbnail (16:9)", gen_size="1536x1024"),
    F("fb-cover", 1640, 624, "Facebook cover", gen_size="1536x1024"),
    F("poster-a3", 2480, 3508, "A3 print poster @300dpi", gen_size="1024x1536"),
    F("poster-18x24", 1800, 2400, "18×24in poster @100dpi (3:4)", gen_size="1024x1536"),
    F("phone-wallpaper", 1170, 2532, "Phone wallpaper", gen_size="1024x1536"),
    F("desktop-wallpaper", 2560, 1440, "Desktop wallpaper (16:9)", gen_size="1536x1024"),
]}

ALIASES = {"story": "ig-story", "post": "ig-post", "square": "ig-square", "tiktok": "reel-cover",
           "reel": "reel-cover", "twitter": "x-post", "x": "x-post", "pinterest": "pin",
           "poster": "poster-18x24", "thumbnail": "yt-thumb", "wallpaper": "phone-wallpaper"}


def get(name: str) -> Format:
    key = ALIASES.get(name, name)
    if key in FORMATS:
        return FORMATS[key]
    if "x" in name and name.replace("x", "").isdigit():
        w, h = (int(v) for v in name.split("x"))
        return Format(name, w, h, "custom", gen_size="1024x1536" if h > w else "1536x1024" if w > h else "1024x1024")
    raise KeyError(f"unknown format {name!r}. Options: {', '.join(FORMATS)} or WIDTHxHEIGHT")
