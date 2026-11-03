"""End to end: Pinterest → moodboard → prompt → image → finished post (+ caption & hashtags)."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import aesthetics, analyze, formats, pinterest, prompt
from .compose import Design, render
from .config import OUT_DIR
from .models import Moodboard
from .providers import GenRequest, generate


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "design"


@dataclass
class Brand:
    handle: str = ""
    palette: list[str] = field(default_factory=list)
    display_font: str = ""
    body_font: str = ""
    logo: str = ""

    @classmethod
    def load(cls, path: str | None) -> "Brand":
        if not path:
            return cls()
        d = json.loads(Path(path).read_text())
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


def research(query: str, limit: int = 24, source: str = "auto", out_dir: Path | None = None) -> tuple[Moodboard, list[str]]:
    pins, log = pinterest.explore(query, limit, source)
    pins = pinterest.download(pins)
    mb = analyze.build_moodboard(query, pins, out_dir)
    if out_dir:
        (Path(out_dir) / "moodboard.json").write_text(json.dumps(mb.to_dict(), indent=2))
    return mb, log


def hashtags(mb: Moodboard | None, aesthetic: str, n: int = 15) -> list[str]:
    a = aesthetics.get(aesthetic)
    words = list(a.keywords) + (mb.keywords if mb else []) + ([mb.query] if mb else [])
    tags, seen = [], set()
    for w in words:
        t = "#" + re.sub(r"[^a-z0-9]", "", w.lower())
        if len(t) > 3 and t not in seen:
            seen.add(t)
            tags.append(t)
    tags += [f"#{a.name.replace('-', '')}", "#aesthetic", "#moodboard", "#pinterestinspired"]
    return list(dict.fromkeys(tags))[:n]


def create(
    subject: str,
    *,
    inspo: str | None = None,
    template: str = "poster",
    fmt: str = "ig-post",
    title: str = "",
    subtitle: str = "",
    body: str = "",
    kicker: str = "",
    handle: str = "",
    cta: str = "",
    aesthetic: str | None = None,
    provider: str | None = None,
    source: str = "auto",
    limit: int = 24,
    use_refs: bool = True,
    background: str | None = None,
    slides: list[dict] | None = None,
    brand: str | None = None,
    out_dir: str | None = None,
    variations: int = 1,
    seed: int | None = None,
) -> dict:
    """Make a finished design. Returns a manifest dict (also written to manifest.json)."""
    f = formats.get(fmt)
    b = Brand.load(brand)
    out = Path(out_dir or OUT_DIR) / f"{time.strftime('%Y%m%d-%H%M%S')}-{slug(title or subject)}"
    out.mkdir(parents=True, exist_ok=True)
    log: list[str] = []

    mb: Moodboard | None = None
    if inspo:
        mb, log = research(inspo, limit, source, out)
    a = aesthetics.get(aesthetic or (mb.aesthetic if mb and mb.pins else None))
    pal = b.palette or (mb.palette if mb and mb.palette else list(a.palette))
    if len(pal) < 3:
        pal = pal + list(a.palette)

    p = prompt.build(subject, mb, a.name, f, template)
    images: list[str] = []
    used = "user-supplied"
    if background:
        images = [x for x in background.split(",") if x]
    else:
        refs = [pp.local_path for pp in (mb.pins if mb else [])
                if pp.local_path][:4] if use_refs else []
        for v in range(max(1, variations)):
            req = GenRequest(prompt=p["prompt"], negative=p["negative"], out=out / f"base-{v + 1}.png",
                             width=f.width if f.width <= 1536 else 1024, height=f.height if f.height <= 1536 else 1536,
                             refs=refs, palette=pal, aesthetic=a.name,
                             seed=(seed + v) if seed is not None else None)
            path, used = generate(req, provider)
            images.append(str(path))
            log.append(f"generated {path.name} with {used}")
            if template == "carousel":
                break  # one cover; the slides get their own images below
        if template == "carousel":  # one picture per slide, so the deck doesn't repeat the cover
            for n, s in enumerate(slides or [], start=1):
                sp = prompt.build(s.get("subject") or f"{subject}, {s.get('title', '')}", mb, a.name, f, "slide")
                req = GenRequest(prompt=sp["prompt"], negative=sp["negative"], out=out / f"slide-{n}.png",
                                 width=f.width if f.width <= 1536 else 1024,
                                 height=f.height if f.height <= 1536 else 1536, refs=refs, palette=pal,
                                 aesthetic=a.name, seed=(seed + n) if seed is not None else None)
                path, used = generate(req, provider)
                images.append(str(path))
                log.append(f"generated {path.name} with {used}")

    finals: list[str] = []
    for i, img in enumerate(images if template not in ("collage", "carousel") else [images[0]]):
        imgs = images if template in ("collage", "carousel") else [img]
        if template == "collage" and mb and len(imgs) < 3:  # collage the generated image with inspo crops
            imgs = imgs + [pp.local_path for pp in mb.pins if pp.local_path][:3]
        ds = Design(template=template, fmt=f, images=imgs, title=title, subtitle=subtitle, body=body,
                    kicker=kicker, handle=handle or b.handle, cta=cta, palette=pal,
                    display_font=b.display_font or a.fonts[0], body_font=b.body_font or a.fonts[1],
                    effects=a.effects, slides=slides or [], logo=b.logo)
        suffix = f"-v{i + 1}" if len(images) > 1 and template not in ("collage", "carousel") else ""
        finals += [str(x) for x in render(ds, out / f"{template}-{f.name}{suffix}.jpg")]

    tags = hashtags(mb, a.name)
    caption = (f"{title or subject}\n\n{subtitle}\n\n" if subtitle else f"{title or subject}\n\n") + " ".join(tags)
    (out / "caption.txt").write_text(caption.strip() + "\n")
    manifest = {
        "subject": subject, "template": template, "format": f.name, "size": [f.width, f.height],
        "aesthetic": a.name, "provider": used, "prompt": p["prompt"], "negative": p["negative"],
        "palette": pal, "outputs": finals, "base_images": images, "caption": str(out / "caption.txt"),
        "hashtags": tags, "dir": str(out), "log": log,
        "moodboard": str(out / "moodboard.jpg") if mb and mb.contact_sheet else None,
        "inspiration": [{"pin": pp.url, "image": pp.image_url, "title": pp.title} for pp in (mb.pins if mb else [])][:24],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
