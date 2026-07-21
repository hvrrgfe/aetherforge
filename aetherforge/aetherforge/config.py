"""AetherForge Configuration System - manages settings, model paths, backends.

AI-native design: all config is machine-readable JSON/YAML, 
can be read/written via tools, no manual config file editing needed.
"""
import os, json, yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

CONFIG_DIR = Path(os.environ.get("AETHERFORGE_HOME", str(Path.home() / ".aetherforge")))
CONFIG_FILE = CONFIG_DIR / "config.yaml"
PROJECTS_DIR = Path(__file__).parent / "projects"
MODELS_DIR = CONFIG_DIR / "models"

@dataclass
class PhysicsConfig:
    enabled: bool = True
    engine: str = "pymunk"  # pymunk, bullet
    gravity_x: float = 0.0
    gravity_y: float = 980.0  # pixels/s^2 downward
    debug_draw: bool = False

@dataclass
class AudioConfig:
    enabled: bool = True
    engine: str = "pygame"  # pygame, simpleaudio, sounddevice
    sample_rate: int = 44100
    channels: int = 2
    master_volume: float = 0.8

@dataclass
class RendererConfig:
    engine: str = "threejs"  # threejs, pyopengl, unity
    width: int = 1024
    height: int = 768
    fov: float = 60.0
    background_color: str = "#1a1a22"

@dataclass
class ImageGenConfig:
    enabled: bool = True
    engine: str = "diffusers"  # diffusers, api, stub
    model_path: str = ""  # path to anything-v5 or other model
    model_id: str = "runwayml/stable-diffusion-v1-5"  # HF model ID fallback
    device: str = "cpu"  # cpu, cuda
    max_resolution: int = 512
    lazy_load: bool = True  # load model on first use

@dataclass
class MusicGenConfig:
    enabled: bool = True
    engine: str = "audiocraft"  # audiocraft, api, stub
    model_id: str = "facebook/musicgen-small"
    device: str = "cpu"
    sample_rate: int = 32000
    lazy_load: bool = True

@dataclass
class AgentConfig:
    """Configuration for the Agent Runtime / Model Router."""
    enabled: bool = True
    endpoint: str = ""
    api_key: str = ""
    model_name: str = "gpt-4"
    max_tokens_per_task: int = 4000
    default_policy: str = "normal"
    approval_mode: str = "high_risk"


@dataclass
class NetworkConfig:
    """Configuration for network source detection and switching."""
    auto_detect: bool = True
    timeout: int = 8
    retries: int = 2
    preferred_source: str = "auto"
    sources: list = None
    proxy: dict = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = [
                {"name": "huggingface", "endpoint": "https://huggingface.co", "enabled": True},
                {"name": "hf_mirror", "endpoint": "https://hf-mirror.com", "enabled": True},
            ]
        if self.proxy is None:
            self.proxy = {"enabled": False, "http": "", "https": ""}

    def to_dict(self):
        return {"auto_detect": self.auto_detect, "timeout": self.timeout,
                "retries": self.retries, "preferred_source": self.preferred_source,
                "sources": self.sources, "proxy": self.proxy}


@dataclass
class AetherForgeConfig:
    version: str = "2.0.0"
    server_host: str = "127.0.0.1"
    server_port: int = 7890
    physics: PhysicsConfig = field(default_factory=PhysicsConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    renderer: RendererConfig = field(default_factory=RendererConfig)
    image_gen: ImageGenConfig = field(default_factory=ImageGenConfig)
    music_gen: MusicGenConfig = field(default_factory=MusicGenConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)

    def to_dict(self):
        return {
            "version": self.version,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "physics": asdict(self.physics),
            "audio": asdict(self.audio),
            "renderer": asdict(self.renderer),
            "image_gen": asdict(self.image_gen),
            "music_gen": asdict(self.music_gen),
            "agent": asdict(self.agent),
        }


_default_config = None

def get_config() -> AetherForgeConfig:
    global _default_config
    if _default_config is not None:
        return _default_config
    cfg = AetherForgeConfig()
    # Try loading from file
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if "physics" in data:
                cfg.physics = PhysicsConfig(**data["physics"])
            if "audio" in data:
                cfg.audio = AudioConfig(**data["audio"])
            if "renderer" in data:
                cfg.renderer = RendererConfig(**data["renderer"])
            if "image_gen" in data:
                cfg.image_gen = ImageGenConfig(**data["image_gen"])
            if "agent" in data:
                cfg.agent = AgentConfig(**data["agent"])
            if "network" in data:
                n = data["network"]
                if n.get("sources"): cfg.network.sources = n["sources"]
                if n.get("proxy"): cfg.network.proxy = n["proxy"]
                cfg.network.auto_detect = n.get("auto_detect", True)
                cfg.network.timeout = n.get("timeout", 8)
                cfg.network.retries = n.get("retries", 2)
            if "music_gen" in data:
                cfg.music_gen = MusicGenConfig(**data["music_gen"])
            for k in ["server_host", "server_port", "version"]:
                if k in data:
                    setattr(cfg, k, data[k])
    except Exception as e:
        print(f"  [config] Warning: Could not load config: {e}")
    _default_config = cfg
    return cfg

def save_config(cfg: AetherForgeConfig = None):
    cfg = cfg or get_config()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg.to_dict(), f, default_flow_style=False, allow_unicode=True)
    return str(CONFIG_FILE)

def validate_torch():
    """Check if torch is available and working."""
    try:
        import torch
        # Quick test
        _ = torch.tensor([1.0])
        return True, torch.__version__
    except Exception as e:
        return False, str(e)

def find_model(path_hint: str = "") -> str:
    """Search for a model file in common locations."""
    search_paths = []
    if path_hint:
        search_paths.append(Path(path_hint))
    search_paths.append(MODELS_DIR / "anything-v5")
    search_paths.append(MODELS_DIR / "stable-diffusion")
    for p in search_paths:
        if p.exists() and (p / "model_index.json").exists():
            return str(p)
        # Check for safetensors files
        if p.exists() and list(p.glob("*.safetensors")):
            return str(p)
    return ""

