# AGENTS.md

This repository is **pinmuse**: a skill, CLI and MCP server that lets an AI agent explore Pinterest
and turn what it learns into original posters, stories, carousels and posts.

## If you are an agent using pinmuse
Read and follow [`skills/pinmuse/SKILL.md`](skills/pinmuse/SKILL.md). Its short version:
`pinmuse suggest` → `pinmuse moodboard` (look at the contact sheet) → `pinmuse create` (or
`generate` + `compose`) → look at the output → deliver files, the caption and pin credits.

## If you are an agent working on this codebase
- Python ≥ 3.10. The only runtime dependencies are Pillow and numpy; HTTP uses stdlib `urllib` (`src/pinmuse/http.py`).
- Layout: `pinterest/` (sources), `analyze.py` (palette, mood, aesthetic scoring), `prompt.py`,
  `providers/` (image models), `compose/` (templates, type, effects), `pipeline.py`, `cli.py`, `mcp_server.py`.
- A new image provider subclasses `providers.base.Provider` and is registered in `providers/__init__.py` (`REGISTRY` and `PRIORITY`).
- A new template is a function `Design -> Image` (or `list[Image]`) added to `compose/layouts.TEMPLATES`.
- Tests: `pytest -q`. They are offline. Never add a test that hits pinterest.com or a paid API.
- Regenerate the README gallery with `python examples/make_samples.py` (offline, procedural).
