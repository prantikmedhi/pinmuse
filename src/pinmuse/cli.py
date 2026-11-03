"""pinmuse CLI — every command prints JSON so any agent can read it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, aesthetics, analyze, formats, pinterest, prompt, providers
from .compose import TEMPLATES, Design, render
from .config import OUT_DIR


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def _pins_out(pins, log):
    return {"count": len(pins), "log": log, "pins": [
        {k: v for k, v in p.to_dict().items() if v not in ("", 0, {}, None)} for p in pins]}


def cmd_search(a):
    pins, log = pinterest.explore(a.query, a.limit, a.source, use_cache=not a.fresh)
    if a.download:
        pins = pinterest.download(pins)
    _print(_pins_out(pins, log))


def cmd_suggest(a):
    _print({"query": a.query, "suggestions": pinterest.suggest(a.query)})


def cmd_moodboard(a):
    out = Path(a.out or OUT_DIR) / ("moodboard-" + "".join(c if c.isalnum() else "-" for c in a.query.lower())[:40])
    out.mkdir(parents=True, exist_ok=True)
    pins, log = pinterest.explore(a.query, a.limit, a.source)
    pins = pinterest.download(pins)
    mb = analyze.build_moodboard(a.query, pins, out)
    d = mb.to_dict()
    (out / "moodboard.json").write_text(json.dumps(d, indent=2))
    d.pop("pins")
    d["pin_count"] = len(pins)
    d["log"] = log
    d["json"] = str(out / "moodboard.json")
    d["tip"] = "Open contact_sheet with your image viewer/Read tool to see the vibe before writing a prompt."
    _print(d)


def _load_mb(path):
    from .models import Moodboard
    return Moodboard.from_dict(json.loads(Path(path).read_text())) if path else None


def cmd_prompt(a):
    mb = _load_mb(a.moodboard)
    _print(prompt.build(a.subject, mb, a.aesthetic, formats.get(a.format), a.template, a.extra or ""))


def cmd_generate(a):
    f = formats.get(a.format)
    a1 = aesthetics.get(a.aesthetic)
    pal = a.palette.split(",") if a.palette else list(a1.palette)
    out = Path(a.out or (Path(OUT_DIR) / "generated.png"))
    req = providers.GenRequest(prompt=a.prompt, negative=a.negative or a1.negative, out=out,
                               width=min(f.width, 1536), height=min(f.height, 1536),
                               refs=[r for r in (a.refs or "").split(",") if r], palette=pal,
                               aesthetic=a1.name, seed=a.seed)
    path, used = providers.generate(req, a.provider)
    _print({"image": str(path), "provider": used})


def cmd_compose(a):
    f = formats.get(a.format)
    a1 = aesthetics.get(a.aesthetic)
    slides = json.loads(Path(a.slides).read_text()) if a.slides and Path(a.slides).exists() else (
        json.loads(a.slides) if a.slides else [])
    ds = Design(template=a.template, fmt=f, images=[i for i in (a.image or "").split(",") if i], title=a.title,
                subtitle=a.subtitle, body=a.body, kicker=a.kicker, handle=a.handle, cta=a.cta,
                palette=a.palette.split(",") if a.palette else list(a1.palette),
                display_font=a.display_font or a1.fonts[0], body_font=a.body_font or a1.fonts[1],
                effects=tuple(a.effects.split(",")) if a.effects is not None else a1.effects, slides=slides,
                logo=a.logo or "")
    out = Path(a.out or (Path(OUT_DIR) / f"{a.template}-{f.name}.jpg"))
    _print({"outputs": [str(p) for p in render(ds, out)]})


def cmd_create(a):
    from .pipeline import create
    slides = json.loads(Path(a.slides).read_text()) if a.slides and Path(a.slides).exists() else (
        json.loads(a.slides) if a.slides else None)
    _print(create(a.subject, inspo=a.inspo, template=a.template, fmt=a.format, title=a.title, subtitle=a.subtitle,
                  body=a.body, kicker=a.kicker, handle=a.handle, cta=a.cta, aesthetic=a.aesthetic,
                  provider=a.provider, source=a.source, limit=a.limit, use_refs=not a.no_refs,
                  background=a.image, slides=slides, brand=a.brand, out_dir=a.out, variations=a.variations,
                  seed=a.seed))


def cmd_boards(a):
    from .pinterest import official
    _print(official.boards() if not a.board else [p.to_dict() for p in official.board_pins(a.board, a.limit)])


def cmd_list(a):
    if a.what == "providers":
        _print(providers.status())
    elif a.what == "aesthetics":
        _print({k: {"palette": v.palette, "fonts": v.fonts, "templates": v.templates, "style": v.style}
                for k, v in aesthetics.PRESETS.items()})
    elif a.what == "formats":
        _print({k: {"size": f"{v.width}x{v.height}", "label": v.label} for k, v in formats.FORMATS.items()})
    else:
        _print(sorted(TEMPLATES))


def cmd_mcp(a):
    from .mcp_server import main
    main()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("pinmuse", description="Pinterest-powered creative engine for AI agents.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search Pinterest (phrase, pin URL, or board URL)")
    s.add_argument("query")
    s.add_argument("-n", "--limit", type=int, default=25)
    s.add_argument("--source", default="auto", help="auto|web|api-anything|browser|official|local:<dir>")
    s.add_argument("--download", action="store_true", help="also cache images locally")
    s.add_argument("--fresh", action="store_true", help="ignore the 6h cache")
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("suggest", help="Pinterest's related searches for an idea")
    s.add_argument("query")
    s.set_defaults(fn=cmd_suggest)

    s = sub.add_parser("moodboard", help="research a query → palette, mood, aesthetic, contact sheet")
    s.add_argument("query")
    s.add_argument("-n", "--limit", type=int, default=24)
    s.add_argument("--source", default="auto")
    s.add_argument("-o", "--out")
    s.set_defaults(fn=cmd_moodboard)

    s = sub.add_parser("prompt", help="write an image prompt from a moodboard")
    s.add_argument("subject")
    s.add_argument("--moodboard", help="moodboard.json path")
    s.add_argument("--aesthetic")
    s.add_argument("-f", "--format", default="ig-post")
    s.add_argument("-t", "--template", default="poster")
    s.add_argument("--extra")
    s.set_defaults(fn=cmd_prompt)

    s = sub.add_parser("generate", help="generate an image with the best available provider")
    s.add_argument("prompt")
    s.add_argument("--provider")
    s.add_argument("--negative")
    s.add_argument("-f", "--format", default="ig-post")
    s.add_argument("--aesthetic")
    s.add_argument("--palette", help="comma-separated hex colours")
    s.add_argument("--refs", help="comma-separated local reference images")
    s.add_argument("--seed", type=int)
    s.add_argument("-o", "--out")
    s.set_defaults(fn=cmd_generate)

    def design_args(s):
        s.add_argument("-t", "--template", default="poster", choices=sorted(TEMPLATES))
        s.add_argument("-f", "--format", default="ig-post")
        s.add_argument("--title", default="")
        s.add_argument("--subtitle", default="")
        s.add_argument("--body", default="")
        s.add_argument("--kicker", default="")
        s.add_argument("--handle", default="")
        s.add_argument("--cta", default="")
        s.add_argument("--aesthetic")
        s.add_argument("--slides", help="carousel slides: JSON list or path to JSON")
        s.add_argument("--image", help="use these image(s) instead of generating (comma-separated)")
        s.add_argument("-o", "--out")

    s = sub.add_parser("compose", help="lay out a finished design from image(s) + text")
    design_args(s)
    s.add_argument("--palette")
    s.add_argument("--display-font")
    s.add_argument("--body-font")
    s.add_argument("--effects", help="comma list: grain,vignette,lightleak,scanlines,duotone ('' for none)")
    s.add_argument("--logo")
    s.set_defaults(fn=cmd_compose)

    s = sub.add_parser("create", help="end to end: inspo → image → finished post + caption")
    s.add_argument("subject", help="what the image should show")
    design_args(s)
    s.add_argument("--inspo", help="Pinterest search / pin URL / board URL / local folder to learn from")
    s.add_argument("--provider")
    s.add_argument("--source", default="auto")
    s.add_argument("-n", "--limit", type=int, default=24)
    s.add_argument("--no-refs", action="store_true", help="don't send pins as reference images")
    s.add_argument("--brand", help="brand.json (handle, palette, fonts, logo)")
    s.add_argument("--variations", type=int, default=1)
    s.add_argument("--seed", type=int)
    s.set_defaults(fn=cmd_create)

    s = sub.add_parser("boards", help="your boards via the official API (PINTEREST_ACCESS_TOKEN)")
    s.add_argument("--board", help="board id → list its pins")
    s.add_argument("-n", "--limit", type=int, default=50)
    s.set_defaults(fn=cmd_boards)

    s = sub.add_parser("list", help="list providers | aesthetics | formats | templates")
    s.add_argument("what", choices=["providers", "aesthetics", "formats", "templates"])
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("mcp", help="run as an MCP server (stdio)")
    s.set_defaults(fn=cmd_mcp)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
        return 0
    except Exception as e:  # noqa: BLE001
        _print({"ok": False, "error": type(e).__name__, "message": str(e)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
