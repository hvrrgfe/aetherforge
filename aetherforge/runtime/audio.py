"""Audio Engine - semantic audio playback using pygame.mixer.

Supports: sound effects, background music layers, volume control,
spatial audio (pan), crossfade transitions.
AI-natively controlled via semantic events, not file paths.
"""
import os, sys, math, threading, time
sys.path.insert(0, ".")
from pathlib import Path
from aetherforge.config import get_config

class AudioEngine:
    """Semantic audio engine. Play sounds by name/type, not file path."""

    def __init__(self):
        self._initialized = False
        self._disabled = False
        self._channels = {}
        self._music_playing = None
        self._layers = {}  # layer_name -> {path, volume, loop}
        self._sound_cache = {}  # name -> Sound object
        self._volume = 1.0
        self._music_volume = 0.7
        self._sfx_volume = 1.0
        self._sound_dir = Path(__file__).parent.parent / "assets" / "sounds"

    def init(self):
        cfg = get_config().audio
        if not cfg.enabled:
            self._disabled = True
            return
        try:
            import pygame
            pygame.mixer.init(frequency=cfg.sample_rate, channels=cfg.channels)
            self._initialized = True
            self._volume = cfg.master_volume
            # Voice channels for simultaneous SFX
            pygame.mixer.set_num_channels(16)
        except Exception as e:
            print(f"  [audio] Failed to init pygame.mixer: {e}")
            self._disabled = True

    def _ensure_init(self):
        if not self._initialized and not self._disabled:
            self.init()

    def load_sound(self, name, file_path):
        """Register a sound by name for AI-friendly access."""
        self._ensure_init()
        if self._disabled:
            return False
        try:
            import pygame
            path = Path(file_path)
            if not path.is_absolute():
                path = self._sound_dir / path
            if path.exists():
                snd = pygame.mixer.Sound(str(path))
                self._sound_cache[name] = snd
                return True
            return False
        except Exception:
            return False

    def play_sound(self, name, volume=1.0, loops=0, pan=0.0):
        """Play a registered sound effect.
        
        Args:
            name: Sound name (pre-registered via load_sound)
            volume: 0.0-1.0
            loops: 0=once, -1=loop
            pan: -1.0 (left) to 1.0 (right), 0=center
        """
        self._ensure_init()
        if self._disabled:
            return {"success": False, "error": "Audio disabled"}

        import pygame
        snd = self._sound_cache.get(name)
        if not snd:
            return {"success": False, "error": f"Sound not found: {name}"}

        ch = snd.play(loops=loops)
        if ch:
            ch.set_volume(max(0, self._sfx_volume * volume * (1 - max(0, pan))),
                          max(0, self._sfx_volume * volume * (1 - max(0, -pan))))
            return {"success": True, "channel": ch.get_busy()}
        return {"success": False, "error": "No free channel"}

    def play_music(self, name, file_path=None, volume=None, loop=True, fade_ms=0):
        """Play background music, crossfading if already playing."""
        self._ensure_init()
        if self._disabled:
            return {"success": False, "error": "Audio disabled"}

        import pygame
        path = file_path or str(self._sound_dir / f"{name}.ogg")
        if not os.path.exists(path):
            path = str(self._sound_dir / f"{name}.wav")
        if not os.path.exists(path):
            # Try registered layer
            layer = self._layers.get(name)
            if layer:
                path = layer.get("path", "")
            if not path or not os.path.exists(path):
                return {"success": False, "error": f"Music file not found: {name}"}

        if fade_ms > 0 and pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade_ms)
            time.sleep(fade_ms / 2000.0)

        pygame.mixer.music.load(path)
        vol = (volume or self._music_volume) * self._volume
        pygame.mixer.music.set_volume(vol)
        pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
        self._music_playing = name
        return {"success": True, "name": name}

    def stop_music(self, fade_ms=0):
        self._ensure_init()
        if self._disabled:
            return {"success": False}
        import pygame
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        self._music_playing = None
        return {"success": True}

    def stop_all(self):
        self._ensure_init()
        if self._disabled:
            return
        import pygame
        pygame.mixer.stop()
        pygame.mixer.music.stop()
        self._music_playing = None

    def set_master_volume(self, vol):
        self._volume = max(0.0, min(1.0, vol))
        if self._initialized:
            import pygame
            pygame.mixer.music.set_volume(self._music_volume * self._volume)

    def set_music_volume(self, vol):
        self._music_volume = max(0.0, min(1.0, vol))
        if self._initialized:
            import pygame
            pygame.mixer.music.set_volume(self._music_volume * self._volume)

    def set_sfx_volume(self, vol):
        self._sfx_volume = max(0.0, min(1.0, vol))

    def register_layer(self, name, path, volume=0.5, loop=True):
        """Register an audio layer for AI semantic control."""
        self._layers[name] = {"path": path, "volume": volume, "loop": loop}

    def get_state(self):
        """Return current audio state as JSON-serializable dict."""
        return {
            "initialized": self._initialized,
            "disabled": self._disabled,
            "master_volume": self._volume,
            "music_volume": self._music_volume,
            "sfx_volume": self._sfx_volume,
            "music_playing": self._music_playing,
            "registered_sounds": list(self._sound_cache.keys()),
            "registered_layers": list(self._layers.keys()),
        }

    def cleanup(self):
        self.stop_all()
        self._sound_cache.clear()
        self._layers.clear()
        self._initialized = False
