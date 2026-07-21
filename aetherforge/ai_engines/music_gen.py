"""AI Music Generation Engine - auto-detect available models, user-selectable.

Auto-detects:
  - MusicGen variants (small/medium/large/melody)
  - Audiocraft cached models
  - Local model paths

User can:
  - list_available_models() -> see all detected models
  - select_model(name) -> switch model
  - generate_music(description) -> uses selected model
"""
import os, sys, json, base64, io, threading, time
from pathlib import Path
from aetherforge.config import get_config, validate_torch

KNOWN_MUSIC_MODELS = {
    "musicgen-small": {
        "hf_id": "facebook/musicgen-small",
        "desc": "MusicGen Small - fastest, good for effects",
        "params": "300M",
    },
    "musicgen-medium": {
        "hf_id": "facebook/musicgen-medium",
        "desc": "MusicGen Medium - balanced quality/speed",
        "params": "1.5B",
    },
    "musicgen-large": {
        "hf_id": "facebook/musicgen-large",
        "desc": "MusicGen Large - best quality, needs 8GB+",
        "params": "3.3B",
    },
    "musicgen-melody": {
        "hf_id": "facebook/musicgen-melody",
        "desc": "MusicGen Melody - melody-conditioned generation",
        "params": "1.5B",
    },
    "audiogen": {
        "hf_id": "facebook/audiogen-medium",
        "desc": "AudioGen - sound effect focused",
        "params": "1.5B",
    },
}


def scan_local_music_models():
    """Scan for locally cached audiocraft/MusicGen models."""
    found = {}
    cache_dirs = [
        Path.home() / ".cache" / "huggingface" / "hub",
        Path(".") / "models",
        Path.home() / "models",
    ]
    for base in cache_dirs:
        if not base.exists():
            continue
        for d in base.iterdir():
            if d.is_dir() and "musicgen" in d.name.lower():
                found[d.name] = {
                    "path": str(d),
                    "source": "local_cache",
                    "desc": f"Local: {d.name}",
                }
    return found


class MusicGenEngine:
    """AI-powered music generation with auto model detection."""

    def __init__(self):
        self._model = None
        self._loaded = False
        self._disabled = False
        self._generated = {}
        self._output_dir = Path(__file__).parent.parent / "assets" / "generated"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._config = get_config().music_gen
        self._current_model_name = "auto"
        self._detected_models = {}

    def list_available_models(self):
        """Scan and return all available music models."""
        models = {}
        # Local cache
        local = scan_local_music_models()
        models.update(local)
        # Known models (check if cached)
        for name, info in KNOWN_MUSIC_MODELS.items():
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            cache_name = "models--" + info["hf_id"].replace("/", "--")
            cached_path = cache_dir / cache_name
            if cached_path.exists():
                models[name] = dict(info, path=str(cached_path), source="huggingface_cache")
            else:
                models[name] = dict(info, path="", source="downloadable")
        self._detected_models = models
        return models

    def select_model(self, name_or_path, force_reload=False):
        """Switch model. Returns immediately (no network)."""
        if name_or_path in KNOWN_MUSIC_MODELS:
            resolved = KNOWN_MUSIC_MODELS[name_or_path]["hf_id"]
        elif name_or_path in self._detected_models:
            resolved = self._detected_models[name_or_path].get("path", name_or_path)
        else:
            resolved = name_or_path
        self._current_model_name = name_or_path
        self._resolved_path = resolved
        self._loaded = False
        return {"success": True, "model": name_or_path, "path": resolved, "loaded": False}

    def init(self, force=False):
        """Non-blocking init. Only checks torch, no network."""
        if self._loaded and not force:
            return True
        if not self._config.enabled:
            self._disabled = True
            return False
        torch_ok, _ = validate_torch()
        if not torch_ok:
            self._disabled = True
            return False
        try:
            import audiocraft
            self._loaded = True
            return True
        except ImportError:
            self._disabled = True
            return False

    def generate_music(self, description, duration=8.0, name=None):
        if self._disabled:
            return {"success": False, "error": "Music generation not available"}

        if not self._loaded:
            return {"success": False, "error": "Model not loaded (check network or see README)"}

        try:
            self._model.set_generation_params(duration=duration)
            wav = self._model.generate([description], progress=True)
            wav_np = wav[0].cpu().numpy()

            import soundfile as sf
            sr = self._config.sample_rate
            music_name = name or f"music_{int(time.time())}.wav"
            if not music_name.endswith(".wav"):
                music_name += ".wav"
            out_path = self._output_dir / music_name
            sf.write(str(out_path), wav_np.T, sr)
            self._generated[music_name] = str(out_path)

            return {
                "success": True,
                "name": music_name,
                "path": str(out_path),
                "duration": duration,
                "sample_rate": sr,
                "model": self._current_model_name,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_sound_effect(self, description, duration=2.0, name=None):
        desc = f"{description}, game sound effect, short"
        return self.generate_music(desc, duration=duration, name=name)

    def list_assets(self):
        assets = []
        for name, path in self._generated.items():
            assets.append({"name": name, "path": path})
        if self._output_dir.exists():
            for f in self._output_dir.glob("*.wav"):
                if f.name not in self._generated:
                    assets.append({"name": f.name, "path": str(f)})
        return assets

    def get_state(self):
        models = self.list_available_models()
        return {
            "loaded": self._loaded,
            "disabled": self._disabled,
            "current_model": self._current_model_name,
            "available_models": list(models.keys()),
            "model_details": {k: {"desc": v.get("desc", ""), "params": v.get("params", ""), "source": v.get("source", "unknown")}
                              for k, v in models.items()},
            "generated_count": len(self._generated),
        }

