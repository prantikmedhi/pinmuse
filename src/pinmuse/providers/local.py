"""Local image models: ComfyUI, AUTOMATIC1111/Forge, 🤗 diffusers, or any CLI you already use."""

from __future__ import annotations

import json
import random
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode

from .. import http
from ..config import setting
from .base import GenRequest, Provider


def _up(url: str, path: str = "") -> bool:
    try:
        http.request("GET", url.rstrip("/") + path, timeout=2, retries=0)
        return True
    except Exception:  # noqa: BLE001
        return False


class A1111Provider(Provider):
    name, kind = "a1111", "local"
    setup = "run AUTOMATIC1111 / Forge with --api (default http://127.0.0.1:7860, or PINMUSE_A1111_URL)"

    @property
    def url(self) -> str:
        return setting("a1111_url") or "http://127.0.0.1:7860"

    def available(self) -> bool:
        return _up(self.url, "/sdapi/v1/sd-models")

    def generate(self, req: GenRequest) -> Path:
        w, h = (int(v) for v in req.size.split("x"))
        scale = int(setting("a1111_max_side") or 1024) / max(w, h)
        data = http.post_json(self.url.rstrip("/") + "/sdapi/v1/txt2img", {
            "prompt": req.prompt, "negative_prompt": req.negative, "width": int(w * scale) // 8 * 8,
            "height": int(h * scale) // 8 * 8, "steps": int(setting("a1111_steps") or 28), "cfg_scale": 6,
            "seed": req.seed if req.seed is not None else -1}, timeout=600)
        return self.save_b64(data["images"][0], req.out)


DEFAULT_COMFY = {
    "3": {"class_type": "KSampler", "inputs": {"seed": "{{seed}}", "steps": 28, "cfg": 6, "sampler_name": "dpmpp_2m",
                                               "scheduler": "karras", "denoise": 1, "model": ["4", 0],
                                               "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "{{ckpt}}"}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": "{{width}}", "height": "{{height}}", "batch_size": 1}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "{{prompt}}", "clip": ["4", 1]}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "{{negative}}", "clip": ["4", 1]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "pinmuse", "images": ["8", 0]}},
}


class ComfyUIProvider(Provider):
    name, kind = "comfyui", "local"
    setup = ("run ComfyUI (default http://127.0.0.1:8188, or PINMUSE_COMFYUI_URL); set PINMUSE_COMFY_CKPT "
             "or PINMUSE_COMFY_WORKFLOW=/path/api-workflow.json with {{prompt}} {{negative}} {{width}} {{height}} {{seed}}")

    @property
    def url(self) -> str:
        return (setting("comfyui_url") or "http://127.0.0.1:8188").rstrip("/")

    def available(self) -> bool:
        return _up(self.url, "/system_stats")

    def _workflow(self, req: GenRequest) -> dict:
        wf_path = setting("comfy_workflow")
        wf = json.loads(Path(wf_path).read_text()) if wf_path else DEFAULT_COMFY
        w, h = (int(v) for v in req.size.split("x"))
        values = {"{{prompt}}": req.prompt, "{{negative}}": req.negative, "{{width}}": w, "{{height}}": h,
                  "{{seed}}": req.seed if req.seed is not None else random.randint(0, 2**31),
                  "{{ckpt}}": setting("comfy_ckpt") or "sd_xl_base_1.0.safetensors"}

        def fill(o):
            if isinstance(o, dict):
                return {k: fill(v) for k, v in o.items()}
            if isinstance(o, list):
                return [fill(v) for v in o]
            if isinstance(o, str):
                if o in values:
                    return values[o]
                for k, v in values.items():
                    o = o.replace(k, str(v))
            return o
        return fill(wf)

    def generate(self, req: GenRequest) -> Path:
        pid = http.post_json(self.url + "/prompt", {"prompt": self._workflow(req), "client_id": "pinmuse"})["prompt_id"]
        for _ in range(600):
            hist = http.get_json(f"{self.url}/history/{pid}")
            if pid in hist:
                for node in hist[pid].get("outputs", {}).values():
                    for img in node.get("images", []):
                        q = urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""),
                                       "type": img.get("type", "output")})
                        return self.save_bytes(http.request("GET", f"{self.url}/view?{q}"), req.out)
                raise RuntimeError("ComfyUI finished without an image output")
            time.sleep(1)
        raise TimeoutError("ComfyUI did not finish in 10 minutes")


class DiffusersProvider(Provider):
    name, kind = "diffusers", "local"
    setup = "pip install diffusers torch transformers accelerate; optional PINMUSE_DIFFUSERS_MODEL (default stabilityai/sdxl-turbo)"

    def available(self) -> bool:
        if not setting("diffusers_model") and not setting("use_diffusers"):
            return False  # opt-in: model download is large
        try:
            import diffusers  # noqa: F401
            import torch  # noqa: F401
            return True
        except ImportError:
            return False

    def generate(self, req: GenRequest) -> Path:
        import torch
        from diffusers import AutoPipelineForText2Image

        model = setting("diffusers_model") or "stabilityai/sdxl-turbo"
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        pipe = AutoPipelineForText2Image.from_pretrained(
            model, torch_dtype=torch.float16 if device != "cpu" else torch.float32).to(device)
        turbo = "turbo" in model or "schnell" in model
        w, h = (int(v) for v in req.size.split("x"))
        s = 768 / max(w, h)
        img = pipe(prompt=req.prompt, negative_prompt=None if turbo else req.negative,
                   width=int(w * s) // 8 * 8, height=int(h * s) // 8 * 8,
                   num_inference_steps=4 if turbo else 30, guidance_scale=0.0 if turbo else 6.0).images[0]
        req.out.parent.mkdir(parents=True, exist_ok=True)
        img.save(req.out)
        return req.out


class CommandProvider(Provider):
    """Wrap ANY image tool: mflux, Draw Things CLI, sd.cpp, a custom script…

    PINMUSE_IMAGE_CMD='mflux-generate --model schnell --prompt {prompt} --width {width} --height {height} --output {out}'
    """

    name, kind = "command", "local"
    setup = "export PINMUSE_IMAGE_CMD='your-tool --prompt {prompt} --out {out} …'"

    def available(self) -> bool:
        cmd = setting("image_cmd")
        return bool(cmd) and shutil.which(shlex.split(cmd)[0]) is not None

    def generate(self, req: GenRequest) -> Path:
        w, h = (int(v) for v in req.size.split("x"))
        tmpl = setting("image_cmd") or ""
        argv = [a.format(prompt=req.prompt, negative=req.negative, width=w, height=h, out=str(req.out),
                         seed=req.seed or 0, refs=",".join(req.refs)) for a in shlex.split(tmpl)]
        req.out.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0 or not req.out.exists():
            # some tools print base64 on stdout
            s = proc.stdout.strip()
            if s and len(s) > 1000:
                return self.save_b64(s, req.out)
            raise RuntimeError(f"image command failed ({proc.returncode}): {proc.stderr[-600:]}")
        return req.out

