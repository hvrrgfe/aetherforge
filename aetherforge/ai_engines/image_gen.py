"""AI Image Generation Engine - auto-detect available models, user-selectable.

Auto-scans:
  - Local paths (anything-v5, SD, FLUX, etc.)
  - HuggingFace model cache
  - Pre-configured model_path from config

User can:
  - list_available_models() -> see all detected models
  - select_model(name) -> switch model on-the-fly
  - generate(prompt) -> uses currently selected model
"""
import os, sys, json, base64, io, threading, time
from pathlib import Path
sys.path.insert(0, ".")
from aetherforge.config import get_config, validate_torch

KNOWN_IMAGE_MODELS = {
    "anything-v5": {
        "hf_id": "stablediffusionapi/anything-v5",
        "type": "sd15",
        "desc": "Anything V5 - anime-style, good for game assets",
    },
    "sd-1.5": {
        "hf_id": "runwayml/stable-diffusion-v1-5",
        "type": "sd15",
        "desc": "Stable Diffusion 1.5 - general purpose",
    },
    "sd-2.1": {
        "hf_id": "stabilityai/stable-diffusion-2-1",
        "type": "sd21",
        "desc": "Stable Diffusion 2.1 - improved quality",
    },
    "sdxl": {
        "hf_id": "stabilityai/stable-diffusion-xl-base-1.0",
        "type": "sdxl",
        "desc": "SDXL - high quality, needs 8GB+ VRAM",
    },
    "sd3": {
        "hf_id": "stabilityai/stable-diffusion-3-medium",
        "type": "sd3",
        "desc": "Stable Diffusion 3 Medium - latest",
    },
    "flux-schnell": {
        "hf_id": "black-forest-labs/FLUX.1-schnell",
        "type": "flux",
        "desc": "FLUX.1 Schnell - fast, high quality",
    },
    "flux-dev": {
        "hf_id": "black-forest-labs/FLUX.1-dev",
        "type": "flux",
        "desc": "FLUX.1 Dev - best quality, needs 12GB+ VRAM",
    },
}


def scan_local_models(search_paths=None):
    found = {}
    if search_paths is None:
        search_paths = [
            Path(".") / "models",
            Path.home() / ".cache" / "huggingface" / "hub",
            Path.home() / "models",
            Path("D:/models"),
            Path("E:/models"),
        ]
        cfg = get_config().image_gen
        if cfg.model_path:
            search_paths.insert(0, Path(cfg.model_path))
    for base in search_paths:
        base = Path(base)
        if not base.exists():
            continue
        for d in base.rglob("model_index.json"):
            parent = d.parent
            name = parent.name
            found[name] = {"path": str(parent), "type": "diffusers", "source": "local"}
        for d in base.iterdir():
            if d.is_dir():
                sfs = list(d.glob("*.safetensors"))
                if sfs:
                    name = d.name
                    if name not in found:
                        found[name] = {
                            "path": str(d),
                            "type": "diffusers" if (d / "model_index.json").exists() else "safetensors",
                            "source": "local",
                        }
        hub_dir = base / "hub"
        if hub_dir.exists():
            for d in hub_dir.iterdir():
                if d.is_dir() and (d / "model_index.json").exists():
                    name = d.name.replace("models--", "").replace("--", "/")
                    found[name] = {"path": str(d), "type": "diffusers", "source": "huggingface_cache"}
    return found


def scan_installed_hf_models():
    available = {}
    for name, info in KNOWN_IMAGE_MODELS.items():
        hf_id = info["hf_id"]
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        cache_name = "models--" + hf_id.replace("/", "--")
        cached_path = cache_dir / cache_name
        if cached_path.exists():
            available[name] = dict(info, path=str(cached_path), source="huggingface_cache")
    return available


class ImageGenEngine:
    def __init__(self):
        self._pipeline = None
        self._pipeline_lock = threading.Lock()
        self._loaded = False
        self._disabled = False
        self._generated = {}
        self._output_dir = Path(__file__).parent.parent / "assets" / "generated"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._config = get_config().image_gen
        self._current_model_name = "auto"
        self._detected_models = {}

    def list_available_models(self):
        models = {}
        local = scan_local_models()
        models.update(local)
        hf = scan_installed_hf_models()
        models.update(hf)
        for name, info in KNOWN_IMAGE_MODELS.items():
            if name not in models:
                models[name] = dict(info, path="", source="downloadable")
        self._detected_models = models
        return models

    def select_model(self, name_or_path, force_reload=False):
        if name_or_path in KNOWN_IMAGE_MODELS:
            resolved = KNOWN_IMAGE_MODELS[name_or_path]["hf_id"]
        elif name_or_path in self._detected_models:
            info = self._detected_models[name_or_path]
            resolved = info.get("path") or info.get("hf_id", name_or_path)
        else:
            resolved = name_or_path

        if resolved == getattr(self, "_resolved_path", None) and not force_reload and self._loaded:
            return {"success": True, "model": name_or_path, "path": resolved, "already_loaded": True}

        self._resolved_path = resolved
        self._current_model_name = name_or_path
        self._loaded = False

        ok = self.init(force=True)
        if ok:
            return {"success": True, "model": name_or_path, "path": resolved, "loaded": True}
        else:
            return {"success": False, "model": name_or_path, "path": resolved, "error": "Failed to load model, check torch/dependencies"}

    def init(self, force=False):
        if self._loaded and not force:
            return True
        if not self._config.enabled:
            self._disabled = True
            return False

        torch_ok, torch_err = validate_torch()
        if not torch_ok:
            self._disabled = True
            return False

        try:
            from diffusers import DiffusionPipeline
            import torch
            model_path = getattr(self, "_resolved_path", None) or self._config.model_path
            if not model_path:
                local = scan_local_models()
                if local:
                    first = list(local.keys())[0]
                    model_path = local[first]["path"]
                    self._current_model_name = first
                else:
                    model_path = self._config.model_id or "runwayml/stable-diffusion-v1-5"
                    self._current_model_name = model_path
            device = self._config.device or "cpu"
            print(f"  [image_gen] Loading: {model_path} on {device}")
            self._pipeline = DiffusionPipeline.from_pretrained(
                model_path, torch_dtype=torch.float32, safety_checker=None
            )
            self._pipeline.to(device)
            self._loaded = True
            return True
        except Exception as e:
            print(f"  [image_gen] Failed: {e}")
            self._disabled = True
            return False

    def generate(self, prompt, negative_prompt="", width=512, height=512,
                 steps=20, guidance_scale=7.5, seed=-1, name=None):
        if self._disabled:
            return {"success": False, "error": "Image generation disabled (torch not available)"}
        if not self._loaded:
            if self._config.lazy_load:
                ok = self.init()
                if not ok:
                    return {"success": False, "error": "Failed to load model"}
            else:
                return {"success": False, "error": "Model not loaded"}
        try:
            import torch
            gen_args = {
                "prompt": prompt,
                "negative_prompt": negative_prompt or None,
                "width": min(width, 1024), "height": min(height, 1024),
                "num_inference_steps": steps, "guidance_scale": guidance_scale,
            }
            if seed >= 0:
                gen_args["generator"] = torch.Generator().manual_seed(seed)
            with self._pipeline_lock:
                result = self._pipeline(**gen_args)
                image = result.images[0]
            img_name = name or f"gen_{int(time.time())}.png"
            if not img_name.endswith(".png"):
                img_name += ".png"
            img_path = self._output_dir / img_name
            image.save(img_path)
            self._generated[img_name] = str(img_path)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return {
                "success": True, "name": img_name, "path": str(img_path),
                "width": image.width, "height": image.height,
                "model": self._current_model_name,
                "data_uri": f"data:image/png;base64,{b64}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_texture(self, prompt, entity_type="object", style="realistic",
                         width=512, height=512, name=None):
        full_prompt = f"{style} texture of a {prompt}, game asset, {entity_type}"
        return self.generate(full_prompt, width=width, height=height, name=name)

    def list_assets(self):
        assets = []
        for name, path in self._generated.items():
            assets.append({"name": name, "path": path})
        if self._output_dir.exists():
            for f in self._output_dir.glob("*.png"):
                if f.name not in self._generated:
                    assets.append({"name": f.name, "path": str(f)})
        return assets

    def get_state(self):
        models = self.list_available_models()
        return {
            "loaded": self._loaded, "disabled": self._disabled,
            "device": self._config.device,
            "current_model": self._current_model_name,
            "available_models": list(models.keys()),
            "model_details": {k: {"desc": v.get("desc", ""), "source": v.get("source", "unknown")}
                              for k, v in models.items()},
            "generated_count": len(self._generated),
            "output_dir": str(self._output_dir),
        }