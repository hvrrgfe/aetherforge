# -*- coding: utf-8 -*-
"""AetherForge Model Manager."""

import os, json, threading, time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from aetherforge.config import MODELS_DIR

CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# Image models: (name, hf_id, desc, params)
KNOWN_IMAGE_MODELS = [
    ("anything-v5", "stablediffusionapi/anything-v5", "Anime style", "1.4B"),
    ("sd-1.5", "runwayml/stable-diffusion-v1-5", "General purpose", "1.4B"),
    ("sd-2.1", "stabilityai/stable-diffusion-2-1", "Improved quality", "1.4B"),
    ("sdxl", "stabilityai/stable-diffusion-xl-base-1.0", "High quality", "2.6B"),
    ("sd3", "stabilityai/stable-diffusion-3-medium", "Latest", "2.0B"),
    ("flux-schnell", "black-forest-labs/FLUX.1-schnell", "Fast", "3.5B"),
    ("flux-dev", "black-forest-labs/FLUX.1-dev", "Best quality", "12B"),
]

# Music models: (name, hf_id, desc, params)
KNOWN_MUSIC_MODELS = [
    ("musicgen-small", "facebook/musicgen-small", "Fastest", "300M"),
    ("musicgen-medium", "facebook/musicgen-medium", "Balanced", "1.5B"),
    ("musicgen-large", "facebook/musicgen-large", "Best quality", "3.3B"),
    ("musicgen-melody", "facebook/musicgen-melody", "Melody", "1.5B"),
    ("audiogen", "facebook/audiogen-medium", "Sound effects", "1.5B"),
]

ALL_KNOWN = KNOWN_IMAGE_MODELS + KNOWN_MUSIC_MODELS


def _scan_local_models():
    found = {}
    for p in [MODELS_DIR, Path.home() / "models"]:
        if not p.exists():
            continue
        for d in p.iterdir():
            if d.is_dir():
                has_ss = list(d.rglob("*.safetensors"))
                has_idx = (d / "model_index.json").exists()
                if has_ss or has_idx:
                    found[d.name] = {"path": str(d)}
    if CACHE_DIR.exists():
        for d in CACHE_DIR.iterdir():
            if d.is_dir() and d.name.startswith("models--"):
                hf = d.name.replace("models--", "").replace("--", "/")
                found[hf] = {"path": str(d), "source": "huggingface_cache"}
    return found


class ModelManager:
    def __init__(self):
        self._download_threads = {}
        self._lock = threading.Lock()

    def list_models(self, model_type=""):
        local = _scan_local_models()
        results = []
        known = KNOWN_IMAGE_MODELS if model_type == "image" else (
            KNOWN_MUSIC_MODELS if model_type == "music" else ALL_KNOWN)
        for name, hf_id, desc, params in known:
            info = {"name": name, "hf_id": hf_id, "desc": desc, "params": params,
                    "status": "not_downloaded"}
            if name in local or hf_id in local:
                info["status"] = "downloaded"
                info["local_path"] = local.get(name, local.get(hf_id, {})).get("path", "")
            with self._lock:
                if name in self._download_threads:
                    t, pr = self._download_threads[name]
                    if t and t.is_alive():
                        info["status"] = "downloading"
            results.append(info)
        order = {"downloaded": 0, "downloading": 1, "not_downloaded": 2}
        results.sort(key=lambda x: order.get(x["status"], 99))
        return results

    def download(self, name, callback=None):
        model = next((m for m in ALL_KNOWN if m[0] == name), None)
        if not model:
            return {"success": False, "error": f"Unknown model: {name}"}
        _, hf_id, _, _ = model
        local = _scan_local_models()
        if name in local or hf_id in local:
            return {"success": True, "message": f"Already downloaded: {name}", "already": True}
        with self._lock:
            if name in self._download_threads:
                t, _ = self._download_threads[name]
                if t and t.is_alive():
                    return {"success": True, "message": f"Already downloading {name}"}
        progress = [0.0]

        def _do_download():
            try:
                from huggingface_hub import snapshot_download
                target = MODELS_DIR / name
                target.mkdir(parents=True, exist_ok=True)
                snapshot_download(repo_id=hf_id, local_dir=str(target),
                                  local_dir_use_symlinks=False, resume_download=True)
                progress[0] = 100.0
            except Exception:
                if callback:
                    callback(name, -1)

        t = threading.Thread(target=_do_download, daemon=True)
        t.start()
        with self._lock:
            self._download_threads[name] = (t, progress)
        return {"success": True, "message": f"Started downloading {name}", "status": "downloading"}

    def delete_model(self, name):
        model = next((m for m in ALL_KNOWN if m[0] == name), None)
        if not model:
            return {"success": False, "error": f"Unknown model: {name}"}
        _, hf_id, _, _ = model
        local = _scan_local_models()
        lp = local.get(name, {}).get("path") or local.get(hf_id, {}).get("path")
        if not lp:
            return {"success": False, "error": f"Model {name} not found locally"}
        p = Path(lp)
        if p.exists():
            import shutil
            shutil.rmtree(p)
            return {"success": True, "message": f"Deleted {name}"}
        return {"success": False, "error": "Path not found"}

    def model_info(self, name):
        for m in self.list_models():
            if m["name"] == name:
                return {"success": True, "data": m}
        return {"success": False, "error": f"Model {name} not found"}

    def download_progress(self):
        res = []
        with self._lock:
            for n, (t, pr) in self._download_threads.items():
                pct = pr[0] if pr else 0.0
                alive = t and t.is_alive()
                res.append({"name": n, "progress": pct,
                    "status": "downloading" if alive else ("complete" if pct >= 100 else "stalled")})
        return res


model_mgr = ModelManager()
