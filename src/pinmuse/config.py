from __future__ import annotations

import json
import os
from pathlib import Path

CACHE_DIR = Path(os.environ.get("PINMUSE_CACHE", Path.home() / ".cache" / "pinmuse"))
CONFIG_PATH = Path(os.environ.get("PINMUSE_CONFIG", Path.home() / ".config" / "pinmuse" / "config.json"))
OUT_DIR = Path(os.environ.get("PINMUSE_OUT", "pinmuse-out"))
FONT_DIR = Path(__file__).parent / "fonts"


def load_config() -> dict:
    """Optional user config. Env vars always win over the file."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def setting(name: str, default: str | None = None) -> str | None:
    """Look up PINMUSE_<NAME> / <NAME> in env, then config.json."""
    for key in (f"PINMUSE_{name.upper()}", name.upper()):
        if os.environ.get(key):
            return os.environ[key]
    return load_config().get(name.lower(), default)
