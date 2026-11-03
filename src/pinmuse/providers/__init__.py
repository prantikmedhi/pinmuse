"""Image generation providers. Bring whatever you have — cloud, local, or none at all.

`auto` picks the first available in PRIORITY. Force one with --provider / PINMUSE_PROVIDER.
"""

from __future__ import annotations

from pathlib import Path

from ..config import setting
from .base import GenRequest, Provider
from .cloud import FalProvider, GeminiProvider, OpenAIProvider, ReplicateProvider, StabilityProvider, TogetherProvider
from .local import A1111Provider, ComfyUIProvider, CommandProvider, DiffusersProvider
from .procedural import ProceduralProvider

REGISTRY: dict[str, type[Provider]] = {p.name: p for p in [
    OpenAIProvider, GeminiProvider, StabilityProvider, ReplicateProvider, FalProvider, TogetherProvider,
    ComfyUIProvider, A1111Provider, DiffusersProvider, CommandProvider, ProceduralProvider,
]}

PRIORITY = ["command", "comfyui", "a1111", "openai", "gemini", "fal", "replicate", "together", "stability",
            "diffusers", "procedural"]


def status() -> list[dict]:
    rows = []
    for name in PRIORITY:
        p = REGISTRY[name]()
        rows.append({"name": name, "available": p.available(), "kind": p.kind, "how": p.setup,
                     "references": p.supports_refs})
    return rows


def pick(name: str | None = None) -> Provider:
    name = name or setting("provider") or "auto"
    if name != "auto":
        if name not in REGISTRY:
            raise KeyError(f"unknown provider {name!r}. Options: auto, {', '.join(PRIORITY)}")
        return REGISTRY[name]()
    for n in PRIORITY:
        p = REGISTRY[n]()
        if p.available():
            return p
    return ProceduralProvider()


def generate(req: GenRequest, provider: str | None = None) -> tuple[Path, str]:
    p = pick(provider)
    return p.generate(req), p.name


__all__ = ["GenRequest", "Provider", "REGISTRY", "PRIORITY", "status", "pick", "generate"]
