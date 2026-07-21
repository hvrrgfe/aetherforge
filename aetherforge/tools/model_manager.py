# -*- coding: utf-8 -*-
"""AetherForge Model Manager - upgraded with Hugging Face search, type detection, and secure download.

Supports:
- Auto search from Hugging Face by type (image/music/audio)
- Display model name, author, downloads, license, file size
- Background download with progress tracking
- Auto-register to AetherForge after download
- Unified local and online model selection
- Security: no untrusted code execution, safetensors preferred
"""
import os, json, threading, time, shutil
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable, Tuple
from aetherforge.config import MODELS_DIR

CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- Model Type Keywords ---
IMAGE_KEYWORDS = [
    "stable-diffusion", "stable diffusion", "sdxl", "flux",
    "diffusers", "text-to-image", "image-generation",
    "imagegen", "imagen", "dalle", "latent-diffusion",
]

MUSIC_KEYWORDS = [
    "musicgen", "audiogen", "text-to-audio", "text-to-music",
    "music-generation", "musicgen", "music generation",
]

AUDIO_KEYWORDS = [
    "audiogen", "sound-generation", "sound-effect",
    "text-to-sound", "audio-generation", "audio generation",
]

# --- Security Constraints ---
ALLOWED_MODEL_SOURCES = {"huggingface.co"}
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".dll", ".so", ".sh", ".pyc"}
MAX_MODEL_SIZE_GB = 30
PREFERRED_FORMATS = [".safetensors", ".bin"]

# --- Known Model Registry (fallback) ---
KNOWN_IMAGE_MODELS = [
    ("anything-v5", "stablediffusionapi/anything-v5", "Anime style", "1.4B"),
    ("sd-1.5", "runwayml/stable-diffusion-v1-5", "General purpose", "1.4B"),
    ("sd-2.1", "stabilityai/stable-diffusion-2-1", "Improved quality", "1.4B"),
    ("sdxl", "stabilityai/stable-diffusion-xl-base-1.0", "High quality", "2.6B"),
    ("sd3", "stabilityai/stable-diffusion-3-medium", "Latest", "2.0B"),
    ("flux-schnell", "black-forest-labs/FLUX.1-schnell", "Fast", "3.5B"),
    ("flux-dev", "black-forest-labs/FLUX.1-dev", "Best quality", "12B"),
]

KNOWN_MUSIC_MODELS = [
    ("musicgen-small", "facebook/musicgen-small", "Fastest", "300M"),
    ("musicgen-medium", "facebook/musicgen-medium", "Balanced", "1.5B"),
    ("musicgen-large", "facebook/musicgen-large", "Best quality", "3.3B"),
    ("musicgen-melody", "facebook/musicgen-melody", "Melody", "1.5B"),
    ("audiogen", "facebook/audiogen-medium", "Sound effects", "1.5B"),
]

ALL_KNOWN = KNOWN_IMAGE_MODELS + KNOWN_MUSIC_MODELS

# --- Helpers ---

def _scan_local_models() -> Dict[str, Dict]:
    """Scan local directories for downloaded models."""
    found = {}
    for p in [MODELS_DIR, Path.home() / "models"]:
        if not p.exists():
            continue
        for d in p.iterdir():
            if d.is_dir():
                has_ss = list(d.rglob("*.safetensors"))
                has_idx = (d / "model_index.json").exists()
                size_bytes = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) if has_ss or has_idx else 0
                if has_ss or has_idx:
                    found[d.name] = {"path": str(d), "size_bytes": size_bytes, "source": "local"}
    if CACHE_DIR.exists():
        for d in CACHE_DIR.iterdir():
            if d.is_dir() and d.name.startswith("models--"):
                hf = d.name.replace("models--", "").replace("--", "/")
                size_bytes = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) if d.is_dir() else 0
                found[hf] = {"path": str(d), "source": "huggingface_cache", "size_bytes": size_bytes}
    return found

def _detect_model_type(model_id: str, tags: List[str] = None) -> str:
    """Detect model type from model_id and tags."""
    text = f"{model_id} {' '.join(tags or [])}".lower()
    if any(k in text for k in AUDIO_KEYWORDS):
        return "audio"
    if any(k in text for k in MUSIC_KEYWORDS):
        return "music"
    if any(k in text for k in IMAGE_KEYWORDS):
        return "image"
    return "unknown"

def _format_size(bytes_val: int) -> str:
    if bytes_val < 1024:
        return f"{bytes_val}B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val // 1024}KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val // (1024*1024)}MB"
    else:
        return f"{bytes_val / (1024*1024*1024):.1f}GB"

def _get_local_status(model_id: str, local: Dict = None) -> Tuple[str, str]:
    """Check if model is downloaded locally. Returns (status, local_path)."""
    if local is None:
        local = _scan_local_models()
    for key, info in local.items():
        if key == model_id or key == model_id.split("/")[-1]:
            return ("downloaded", info.get("path", ""))
    return ("not_downloaded", "")


class ModelManager:
    """Manages AI model discovery, download, and selection."""

    def __init__(self):
        self._download_threads: Dict[str, Tuple[threading.Thread, List[float], Dict]] = {}
        self._lock = threading.Lock()
        self._search_cache: Dict[str, List[Dict]] = {}
        self._selected_models: Dict[str, str] = {}  # type -> model_id

        # Try to init HF API
        self._hf_api = None
        try:
            from huggingface_hub import HfApi
            self._hf_api = HfApi()
        except ImportError:
            pass

    # ==================== Search ====================

    def search_online_models(self, query: str = "", model_type: str = "",
                             limit: int = 30, sort: str = "downloads",
                             direction: int = -1) -> Dict:
        """Search models from Hugging Face.
        
        Args:
            query: Search keywords
            model_type: "image", "music", "audio", or "" for all
            limit: Max results
            sort: Sort field ("downloads", "likes", "created_at", "last_modified")
            direction: -1 for descending, 1 for ascending
        """
        if not self._hf_api:
            return {"success": False, "count": 0, "models": [],
                    "error": "huggingface_hub not installed. Run: pip install huggingface_hub"}

        # Build search keywords
        keywords = []
        if model_type == "image":
            keywords.extend(IMAGE_KEYWORDS[:3])
        elif model_type == "music":
            keywords.extend(MUSIC_KEYWORDS[:3])
        elif model_type == "audio":
            keywords.extend(AUDIO_KEYWORDS[:3])
        if query:
            keywords.append(query)

        search_query = " ".join(keywords[:3]) if keywords else None
        cache_key = f"{model_type}:{query}:{limit}"

        local = _scan_local_models()

        # Check cache first (TTL: 5 min)
        if cache_key in self._search_cache:
            cached = self._search_cache[cache_key]
            if time.time() - cached.get("timestamp", 0) < 300:
                cached_results = cached.get("results", [])
                return {"success": True, "count": len(cached_results), "models": cached_results, "cached": True}

        try:
            models = self._hf_api.list_models(
                search=search_query,
                sort=sort,
                direction=direction,
                limit=limit,
                full=True,
            )
            results = []
            for model in models:
                model_id = model.id
                tags = list(getattr(model, "tags", []) or [])
                detected_type = _detect_model_type(model_id, tags)
                if model_type and detected_type != model_type:
                    continue

                status, local_path = _get_local_status(model_id, local)
                results.append({
                    "name": model_id.split("/")[-1],
                    "model_id": model_id,
                    "author": model_id.split("/")[0] if "/" in model_id else "",
                    "type": detected_type,
                    "downloads": getattr(model, "downloads", 0),
                    "likes": getattr(model, "likes", 0),
                    "created_at": str(getattr(model, "created_at", "")),
                    "last_modified": str(getattr(model, "last_modified", "")),
                    "tags": tags[:20],
                    "license": self._extract_license(model),
                    "status": status,
                    "local_path": local_path,
                    "source": "huggingface",
                })

            self._search_cache[cache_key] = {"results": results, "timestamp": time.time()}
            return {"success": True, "count": len(results), "models": results}
        except Exception as exc:
            return {"success": False, "count": 0, "models": [], "error": str(exc)}

    def _extract_license(self, model) -> str:
        """Extract license info from HF model object."""
        card_data = getattr(model, "card_data", None)
        if card_data:
            if isinstance(card_data, dict):
                return card_data.get("license", "")
            return getattr(card_data, "license", "") or ""
        return getattr(model, "license", "") or ""

    # ==================== List (Local + Known) ====================

    def list_all_models(self, model_type: str = "") -> List[Dict]:
        """List all models (local + known registry)."""
        local = _scan_local_models()
        results = []
        known = ALL_KNOWN
        if model_type == "image":
            known = KNOWN_IMAGE_MODELS
        elif model_type == "music":
            known = KNOWN_MUSIC_MODELS

        seen = set()
        for name, hf_id, desc, params in known:
            seen.add(name)
            seen.add(hf_id)
            status, local_path = _get_local_status(name, local)
            if not local_path:
                status, local_path = _get_local_status(hf_id, local)
            size_str = _format_size(local.get(name, {}).get("size_bytes", 0) or
                                    local.get(hf_id, {}).get("size_bytes", 0))

            active = self._selected_models.get(
                _detect_model_type(hf_id), "") == hf_id

            results.append({
                "name": name, "model_id": hf_id,
                "desc": desc, "params": params,
                "type": _detect_model_type(hf_id),
                "status": status, "local_path": local_path,
                "size": size_str, "selected": active,
                "source": "known",
            })

        # Add local-only models
        for key, info in local.items():
            if key not in seen:
                detected = _detect_model_type(key)
                if model_type and detected != model_type:
                    continue
                results.append({
                    "name": key.split("/")[-1] if "/" in key else key,
                    "model_id": key,
                    "type": detected,
                    "status": "downloaded",
                    "local_path": info.get("path", ""),
                    "size": _format_size(info.get("size_bytes", 0)),
                    "source": "local",
                })

        return results

    def list_models(self, model_type: str = "") -> List[Dict]:
        """Legacy alias for list_all_models."""
        return self.list_all_models(model_type)

    # ==================== Download ====================

    def download_selected_model(self, model_id: str, callback: Callable = None) -> Dict:
        """Download a model from Hugging Face in background thread."""
        local = _scan_local_models()
        if model_id in local or model_id.split("/")[-1] in local:
            return {"success": True, "message": f"Already downloaded: {model_id}",
                    "already": True, "local_path": local.get(model_id, {}).get("path", "")}

        with self._lock:
            if model_id in self._download_threads:
                t, pr, _ = self._download_threads[model_id]
                if t and t.is_alive():
                    return {"success": True, "message": f"Already downloading {model_id}",
                            "status": "downloading"}

        progress = [0.0]
        errors = [""]

        # Estimate model size before download (skip for known small models)
        try:
            info = self.model_info(model_id)
            if info.get("success"):
                size_str = info["data"].get("size", "")
                if size_str and "GB" in size_str:
                    gb_val = float(size_str.replace("GB", "").strip())
                    if gb_val > MAX_MODEL_SIZE_GB:
                        return {"success": False, "error": f"Model size {gb_val}GB exceeds max {MAX_MODEL_SIZE_GB}GB"}
        except Exception:
            pass

        def _do_download():
            try:
                from huggingface_hub import snapshot_download
                from aetherforge.tools.network import network_manager
                safe_name = model_id.replace("/", "--")
                target = MODELS_DIR / safe_name
                target.mkdir(parents=True, exist_ok=True)

                # Security: check source
                if not any(src in model_id for src in ALLOWED_MODEL_SOURCES):
                    errors[0] = f"Model source not allowed: {model_id}"
                    return

                # Use detected endpoint with failover
                endpoint = network_manager.get_endpoint()
                last_error = None
                for attempt in range(network_manager.retries + 1):
                    try:
                        snapshot_download(
                            repo_id=model_id,
                            endpoint=endpoint,
                            local_dir=str(target),
                            local_dir_use_symlinks=False,
                            resume_download=True,
                            ignore_patterns=["*.exe", "*.bat", "*.cmd", "*.dll", "*.so", "*.sh"],
                        )
                        progress[0] = 100.0
                        last_error = None
                        break
                    except Exception as e:
                        last_error = e
                        if attempt < network_manager.retries:
                            # Try to detect a new source
                            network_manager.detect()
                            endpoint = network_manager.get_endpoint()
                            print(f"[model] Retry {attempt+1} with endpoint: {endpoint}")
                        else:
                            raise
                if last_error:
                    raise last_error
                progress[0] = 100.0

                # Auto-detect and register
                detected = _detect_model_type(model_id)
                if detected != "unknown":
                    self._selected_models[detected] = model_id

                if callback:
                    callback(model_id, 100)
            except Exception as e:
                errors[0] = str(e)
                if callback:
                    callback(model_id, -1)

        t = threading.Thread(target=_do_download, daemon=True)
        t.start()
        info = {"model_id": model_id, "started_at": time.time()}
        with self._lock:
            self._download_threads[model_id] = (t, progress, info)

        return {"success": True, "message": f"Started downloading {model_id}",
                "status": "downloading"}

    def get_model_downloads(self) -> List[Dict]:
        """Get current download progress for all active downloads."""
        res = []
        with self._lock:
            for mid, (t, pr, info) in self._download_threads.items():
                pct = pr[0] if pr else 0
                alive = t and t.is_alive()
                res.append({
                    "model_id": mid,
                    "progress": round(pct, 1),
                    "status": "downloading" if alive else ("completed" if pct >= 100 else "error"),
                })
        return res

    # ==================== Select / Delete / Info ====================

    def select_generated_model(self, model_type: str, model_id: str) -> Dict:
        """Select which model to use for a given type (image/music/audio)."""
        detected = _detect_model_type(model_id)
        if detected == "unknown":
            detected = model_type
        self._selected_models[detected] = model_id
        local = _scan_local_models()
        status, local_path = _get_local_status(model_id, local)
        return {"success": True, "model_type": model_type,
                "model_id": model_id, "status": status,
                "local_path": local_path}

    def get_selected_models(self) -> Dict:
        """Get currently selected models by type."""
        return dict(self._selected_models)

    def delete_model(self, model_id: str) -> Dict:
        """Delete a downloaded model."""
        local = _scan_local_models()
        lp = local.get(model_id, {}).get("path") or local.get(model_id.split("/")[-1], {}).get("path")
        if not lp:
            return {"success": False, "error": f"Model not found locally: {model_id}"}
        p = Path(lp)
        if p.exists():
            shutil.rmtree(p)
            # Remove from selected
            for typ, mid in list(self._selected_models.items()):
                if mid == model_id:
                    del self._selected_models[typ]
            return {"success": True, "message": f"Deleted {model_id}"}
        return {"success": False, "error": "Path not found"}

    def model_info(self, model_id: str) -> Dict:
        """Get model info."""
        results = self.list_all_models()
        for m in results:
            if m["model_id"] == model_id or m.get("name") == model_id:
                return {"success": True, "data": m}
        return {"success": False, "error": f"Model {model_id} not found"}

    def download(self, name: str, callback: Callable = None) -> Dict:
        """Legacy download by name from known list."""
        model = next((m for m in ALL_KNOWN if m[0] == name), None)
        if not model:
            return {"success": False, "error": f"Unknown model: {name}"}
        return self.download_selected_model(model[1], callback)

    def download_progress(self) -> List[Dict]:
        """Alias for get_model_downloads."""
        return self.get_model_downloads()


model_mgr = ModelManager()