# Contributing to pinmuse

Thanks for helping. New aesthetics, templates, formats and image providers are the most wanted PRs.

## Setup

```bash
git clone https://github.com/prantikmedhi/pinmuse && cd pinmuse
pip install -e ".[dev,mcp]"
pytest -q
```

## Ground rules

- Runtime dependencies stay at **Pillow + numpy**. HTTP goes through `src/pinmuse/http.py` (stdlib `urllib`).
- Tests are offline. Never add a test that hits pinterest.com or a paid API; use `tests/fixtures/`.
- Every CLI command prints JSON. Errors are `{"ok": false, "error": ..., "message": ...}`.
- Lint: `ruff check src tests examples --select E,F,W --ignore E501`.

## Adding things

| You want to add | Where |
|---|---|
| An image provider | subclass `providers.base.Provider`, register it in `providers/__init__.py` (`REGISTRY` and `PRIORITY`) |
| A template | a function `Design -> Image` (or `list[Image]`) in `compose/layouts.TEMPLATES` |
| An aesthetic | a preset in `aesthetics.py`, plus a line in `skills/pinmuse/references/aesthetics.md` |
| A platform format | `formats.py` |

## Visual changes

Attach before/after images to the PR. Regenerate the offline gallery with `python examples/make_samples.py`
and README media with `python examples/make_media.py`.
