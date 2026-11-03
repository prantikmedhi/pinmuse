"""Hosted image models. Each one is enabled just by having its key in the environment."""

from __future__ import annotations

import base64
import mimetypes
import time
from pathlib import Path

from .. import http
from ..config import setting
from .base import GenRequest, Provider


def _ref_bytes(paths: list[str], n: int = 4) -> list[tuple[str, bytes, str]]:
    out = []
    for p in paths[:n]:
        f = Path(p)
        if f.exists():
            out.append((f.name, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "image/jpeg"))
    return out


class OpenAIProvider(Provider):
    """OpenAI Images (gpt-image family). Also Azure OpenAI (OPENAI_BASE_URL=https://<resource>.openai.azure.com/openai/v1,
    model = deployment name) and any other OpenAI-compatible server."""

    name, kind, supports_refs = "openai", "cloud", True
    setup = "export OPENAI_API_KEY=…  (optional PINMUSE_OPENAI_MODEL, OPENAI_BASE_URL)"

    def available(self) -> bool:
        return bool(setting("openai_api_key"))

    def generate(self, req: GenRequest) -> Path:
        base = (setting("openai_base_url") or "https://api.openai.com/v1").rstrip("/")
        model = setting("openai_model") or "gpt-image-1"
        auth = {"Authorization": f"Bearer {setting('openai_api_key')}"}
        quality = setting("openai_quality") or "high"
        refs = _ref_bytes(req.refs)
        if refs:  # reference-guided: Pinterest pins steer the style directly
            body, ctype = http.multipart(
                {"model": model, "prompt": req.prompt, "size": req.size, "quality": quality, "n": 1},
                [("image[]", name, data, mime) for name, data, mime in refs])
            resp = http.request("POST", f"{base}/images/edits", data=body,
                                headers={**auth, "Content-Type": ctype}, timeout=300)
            import json
            data = json.loads(resp)
        else:
            data = http.post_json(f"{base}/images/generations",
                                  {"model": model, "prompt": req.prompt, "size": req.size, "quality": quality, "n": 1},
                                  headers=auth, timeout=300)
        item = data["data"][0]
        if item.get("b64_json"):
            return self.save_b64(item["b64_json"], req.out)
        return self.save_bytes(http.request("GET", item["url"]), req.out)


class GeminiProvider(Provider):
    """Google Gemini image models ("Nano Banana") — great at following reference images."""

    name, kind, supports_refs = "gemini", "cloud", True
    setup = "export GEMINI_API_KEY=…  (optional PINMUSE_GEMINI_MODEL)"

    def available(self) -> bool:
        return bool(setting("gemini_api_key") or setting("google_api_key"))

    def generate(self, req: GenRequest) -> Path:
        key = setting("gemini_api_key") or setting("google_api_key")
        model = setting("gemini_model") or "gemini-2.5-flash-image"
        parts: list[dict] = [{"text": req.prompt + (f" Avoid: {req.negative}." if req.negative else "")}]
        for _, data, mime in _ref_bytes(req.refs, 3):
            parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}})
        if len(parts) > 1:
            parts[0]["text"] = ("Use the attached images only as style and mood references (palette, lighting, "
                                "texture). Create an original image: " + parts[0]["text"])
        body = {"contents": [{"parts": parts}],
                "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": req.aspect}}}
        data = http.post_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              body, headers={"x-goog-api-key": key}, timeout=300)
        for cand in data.get("candidates", []):
            for part in (cand.get("content") or {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return self.save_b64(inline["data"], req.out)
        raise RuntimeError(f"Gemini returned no image: {str(data)[:400]}")


class StabilityProvider(Provider):
    name, kind = "stability", "cloud"
    setup = "export STABILITY_API_KEY=…  (optional PINMUSE_STABILITY_ENDPOINT=core|ultra|sd3)"

    def available(self) -> bool:
        return bool(setting("stability_api_key"))

    def generate(self, req: GenRequest) -> Path:
        endpoint = setting("stability_endpoint") or "core"
        body, ctype = http.multipart({"prompt": req.prompt, "negative_prompt": req.negative or None,
                                      "aspect_ratio": req.aspect, "output_format": "png",
                                      "seed": req.seed}, [])
        img = http.request("POST", f"https://api.stability.ai/v2beta/stable-image/generate/{endpoint}", data=body,
                           headers={"Authorization": f"Bearer {setting('stability_api_key')}",
                                    "Accept": "image/*", "Content-Type": ctype}, timeout=300)
        return self.save_bytes(img, req.out)


class ReplicateProvider(Provider):
    name, kind = "replicate", "cloud"
    setup = "export REPLICATE_API_TOKEN=…  (optional PINMUSE_REPLICATE_MODEL, default black-forest-labs/flux-schnell)"

    def available(self) -> bool:
        return bool(setting("replicate_api_token"))

    def generate(self, req: GenRequest) -> Path:
        model = setting("replicate_model") or "black-forest-labs/flux-schnell"
        auth = {"Authorization": f"Bearer {setting('replicate_api_token')}"}
        pred = http.post_json(f"https://api.replicate.com/v1/models/{model}/predictions",
                              {"input": {"prompt": req.prompt, "aspect_ratio": req.aspect, "output_format": "png"}},
                              headers={**auth, "Prefer": "wait"}, timeout=300)
        for _ in range(120):
            if pred.get("status") in ("succeeded", "failed", "canceled"):
                break
            time.sleep(2)
            pred = http.get_json(pred["urls"]["get"], headers=auth)
        if pred.get("status") != "succeeded":
            raise RuntimeError(f"Replicate prediction {pred.get('status')}: {pred.get('error')}")
        out = pred["output"]
        url = out[0] if isinstance(out, list) else out
        return self.save_bytes(http.request("GET", url), req.out)


class FalProvider(Provider):
    name, kind = "fal", "cloud"
    setup = "export FAL_KEY=…  (optional PINMUSE_FAL_MODEL, default fal-ai/flux/schnell)"

    def available(self) -> bool:
        return bool(setting("fal_key"))

    def generate(self, req: GenRequest) -> Path:
        model = setting("fal_model") or "fal-ai/flux/schnell"
        r = req.height / req.width
        size = ("portrait_16_9" if r > 1.6 else "portrait_4_3" if r > 1.1 else
                "landscape_16_9" if r < .62 else "landscape_4_3" if r < .9 else "square_hd")
        data = http.post_json(f"https://fal.run/{model}", {"prompt": req.prompt, "image_size": size,
                                                           "num_images": 1, "seed": req.seed},
                              headers={"Authorization": f"Key {setting('fal_key')}"}, timeout=300)
        return self.save_bytes(http.request("GET", data["images"][0]["url"]), req.out)


class TogetherProvider(Provider):
    name, kind = "together", "cloud"
    setup = "export TOGETHER_API_KEY=…  (optional PINMUSE_TOGETHER_MODEL)"

    def available(self) -> bool:
        return bool(setting("together_api_key"))

    def generate(self, req: GenRequest) -> Path:
        w, h = (int(v) for v in req.size.split("x"))
        data = http.post_json("https://api.together.xyz/v1/images/generations",
                              {"model": setting("together_model") or "black-forest-labs/FLUX.1-schnell",
                               "prompt": req.prompt, "width": w, "height": h, "steps": 4, "n": 1,
                               "response_format": "b64_json"},
                              headers={"Authorization": f"Bearer {setting('together_api_key')}"}, timeout=300)
        return self.save_b64(data["data"][0]["b64_json"], req.out)
