# AetherForge Engine Core Package
# Provides compatibility aliases and convenience re-exports.
from aetherforge.core.world_model import WorldModel
from aetherforge.core.rules import Rule, RuleTriggerType

# Runtime re-exports
from aetherforge.runtime.physics import PhysicsEngine
from aetherforge.runtime.audio import AudioEngine
from aetherforge.runtime.game_loop import GameRuntime

# Renderer
from aetherforge.renderer import SceneGraph3D

# AI engines
from aetherforge.ai_engines.image_gen import ImageGenEngine
from aetherforge.ai_engines.music_gen import MusicGenEngine

# Model manager
from aetherforge.tools.model_manager import model_mgr

__all__ = [
    "WorldModel", "Rule", "RuleTriggerType",
    "PhysicsEngine", "AudioEngine", "GameRuntime",
    "SceneGraph3D",
    "ImageGenEngine", "MusicGenEngine",
    "model_mgr",
]
