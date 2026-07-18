"""EngineTools V2 - extends EngineTools with physics, audio, 3D, and AI tools.

All tools return ToolResult for consistent MCP/API access.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aetherforge.api.tools import EngineTools, ToolResult
from aetherforge.runtime.physics import PhysicsEngine
from aetherforge.runtime.audio import AudioEngine
from aetherforge.renderer import SceneGraph3D, MeshData, Transform3D, Vector3, Light3D, Camera3D
from aetherforge.ai_engines.image_gen import ImageGenEngine
from aetherforge.ai_engines.music_gen import MusicGenEngine
from aetherforge.config import get_config


class EngineToolsV2(EngineTools):
    """Extended engine tools with Physics, Audio, 3D, and AI capabilities."""

    def __init__(self, world):
        super().__init__(world)
        self.physics = PhysicsEngine(world)
        self.audio = AudioEngine()
        self.scene_3d = SceneGraph3D(world)
        self.image_gen = ImageGenEngine()
        self.music_gen = MusicGenEngine()

    # ==================== PHYSICS TOOLS ====================

    def init_physics(self):
        try:
            self.physics.init()
            return ToolResult(True, {"initialized": not self.physics._disabled})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    def add_physics_body(self, entity_id, shape="box", width=32, height=32,
                          mass=1.0, dynamic=True, friction=0.5, elasticity=0.2):
        pos = None
        ent = self.world.get_entity(entity_id)
        if ent:
            pos = ent.position
        result = self.physics.add_body(entity_id, shape=shape, width=width,
                                        height=height, mass=mass, dynamic=dynamic,
                                        friction=friction, elasticity=elasticity,
                                        position=pos)
        return ToolResult(result.get("success", False), data=result)

    def remove_physics_body(self, entity_id):
        ok = self.physics.remove_body(entity_id)
        return ToolResult(ok, {"entity_id": entity_id}) if ok else ToolResult(False, error=f"Body {entity_id} not found")

    def apply_force(self, entity_id, fx=0.0, fy=0.0):
        ok = self.physics.apply_force(entity_id, fx, fy)
        return ToolResult(True, {"entity_id": entity_id, "force": {"x": fx, "y": fy}}) if ok else ToolResult(False, error="Body not found")

    def set_gravity(self, gx=0.0, gy=980.0):
        ok = self.physics.set_gravity(gx, gy)
        return ToolResult(True, {"gravity": {"x": gx, "y": gy}})

    def ray_cast(self, start_x, start_y, end_x, end_y):
        hit_id = self.physics.ray_cast(start_x, start_y, end_x, end_y)
        return ToolResult(True, {"hit_entity_id": hit_id, "start": {"x": start_x, "y": start_y}, "end": {"x": end_x, "y": end_y}})

    def get_physics_info(self, entity_id):
        info = self.physics.get_body_info(entity_id)
        if info:
            return ToolResult(True, info)
        return ToolResult(False, error=f"No physics body for {entity_id}")

    # ==================== AUDIO TOOLS ====================

    def init_audio(self):
        try:
            self.audio.init()
            return ToolResult(True, {"initialized": not self.audio._disabled})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    def load_sound(self, name, file_path):
        ok = self.audio.load_sound(name, file_path)
        return ToolResult(True, {"name": name, "path": file_path}) if ok else ToolResult(False, error=f"Failed to load sound: {name}")

    def play_sound(self, name, volume=1.0, loops=0, pan=0.0):
        result = self.audio.play_sound(name, volume, loops, pan)
        return ToolResult(result.get("success", False), data=result)

    def play_music(self, name, file_path=None, volume=None, loop=True, fade_ms=0):
        result = self.audio.play_music(name, file_path, volume, loop, fade_ms)
        return ToolResult(result.get("success", False), data=result)

    def stop_music(self, fade_ms=0):
        result = self.audio.stop_music(fade_ms)
        return ToolResult(result.get("success", False), data=result)

    def set_audio_volume(self, master=None, music=None, sfx=None):
        if master is not None:
            self.audio.set_master_volume(master)
        if music is not None:
            self.audio.set_music_volume(music)
        if sfx is not None:
            self.audio.set_sfx_volume(sfx)
        return ToolResult(True, {"master": self.audio._volume, "music": self.audio._music_volume, "sfx": self.audio._sfx_volume})

    def get_audio_state(self):
        return ToolResult(True, self.audio.get_state())

    # ==================== 3D TOOLS ====================

    def set_3d_mesh(self, entity_id, geometry="box", color="#888888",
                     texture="", emissive="#000000", metalness=0.0,
                     roughness=0.8, transparent=False, opacity=1.0,
                     wireframe=False):
        md = MeshData(geometry=geometry, color=color, texture=texture,
                      emissive=emissive, metalness=metalness, roughness=roughness,
                      transparent=transparent, opacity=opacity, wireframe=wireframe)
        self.scene_3d.set_mesh(entity_id, md)
        return ToolResult(True, {"entity_id": entity_id, "mesh": md.to_dict()})

    def set_3d_transform(self, entity_id, x=0.0, y=0.0, z=0.0,
                          rx=0.0, ry=0.0, rz=0.0, sx=1.0, sy=1.0, sz=1.0):
        tf = Transform3D(position=Vector3(x, y, z),
                         rotation=Vector3(rx, ry, rz),
                         scale=Vector3(sx, sy, sz))
        self.scene_3d.set_transform(entity_id, tf)
        return ToolResult(True, {"entity_id": entity_id, "transform": tf.to_dict()})

    def add_3d_light(self, light_type="directional", color="#ffffff",
                      intensity=1.0, px=0.0, py=10.0, pz=10.0, shadow=False):
        light = Light3D(light_type=light_type, color=color, intensity=intensity,
                        position=Vector3(px, py, pz), shadow=shadow)
        idx = self.scene_3d.add_light(light)
        return ToolResult(True, {"light_index": idx, "light": light.to_dict()})

    def set_3d_camera(self, px=0.0, py=0.0, pz=10.0, tx=0.0, ty=0.0, tz=0.0,
                       fov=60.0, orthographic=False):
        cam = Camera3D(position=Vector3(px, py, pz), target=Vector3(tx, ty, tz),
                       fov=fov, orthographic=orthographic)
        self.scene_3d.set_camera(cam)
        return ToolResult(True, {"camera": cam.to_dict()})

    def get_3d_state(self):
        state = self.scene_3d.get_3d_state()
        state["tick"] = self.world.tick
        state["game_time"] = self.world.game_time
        return ToolResult(True, state)

    # ==================== AI IMAGE GEN TOOLS ====================

    def init_image_gen(self):
        try:
            ok = self.image_gen.init()
            return ToolResult(True, {"ready": ok, "state": self.image_gen.get_state()})
        except Exception as ex:
            return ToolResult(True, {"ready": False, "error": str(ex)})

    def generate_image(self, prompt, negative_prompt="", width=512, height=512,
                        steps=20, guidance_scale=7.5, seed=-1, name=None):
        result = self.image_gen.generate(prompt, negative_prompt, width, height,
                                          steps, guidance_scale, seed, name)
        ok = result.get("success", False)
        return ToolResult(ok, data={
            "name": result.get("name"),
            "path": result.get("path"),
            "width": result.get("width"),
            "height": result.get("height"),
            "model": result.get("model"),
            "error": result.get("error"),
        }, error=result.get("error") if not ok else None)

    def generate_texture(self, prompt, entity_type="object", style="realistic",
                          width=512, height=512, name=None):
        result = self.image_gen.generate_texture(prompt, entity_type, style, width, height, name)
        ok = result.get("success", False)
        return ToolResult(ok, data={
            "name": result.get("name"),
            "path": result.get("path"),
            "model": result.get("model"),
            "error": result.get("error"),
        }, error=result.get("error") if not ok else None)

    def list_image_models(self):
        """List all available image generation models (local + HF cache + known)."""
        models = self.image_gen.list_available_models()
        state = self.image_gen.get_state()
        return ToolResult(True, {
            "current_model": state.get("current_model"),
            "available_models": models,
            "count": len(models),
        })

    def select_image_model(self, name_or_path):
        """Switch image generation model by name or path.
        
        Examples:
          - select_image_model("anything-v5")      # known model
          - select_image_model("sdxl")             # known model
          - select_image_model("D:/models/my-sd")  # local path
        """
        result = self.image_gen.select_model(name_or_path)
        ok = result.get("success", False)
        state = self.image_gen.get_state()
        return ToolResult(ok, data={
            "model": name_or_path,
            "current_model": state.get("current_model"),
            "loaded": state.get("loaded"),
            "disabled": state.get("disabled"),
        }, error=result.get("error") if not ok else None)

    # ==================== AI MUSIC GEN TOOLS ====================

    def init_music_gen(self):
        try:
            ok = self.music_gen.init()
            return ToolResult(True, {"ready": ok, "state": self.music_gen.get_state()})
        except Exception as ex:
            return ToolResult(True, {"ready": False, "error": str(ex)})

    def generate_music(self, description, duration=8.0, name=None):
        result = self.music_gen.generate_music(description, duration, name)
        ok = result.get("success", False)
        return ToolResult(ok, data={
            "name": result.get("name"),
            "path": result.get("path"),
            "duration": result.get("duration"),
            "model": result.get("model"),
            "error": result.get("error"),
        }, error=result.get("error") if not ok else None)

    def generate_sound_effect(self, description, duration=2.0, name=None):
        result = self.music_gen.generate_sound_effect(description, duration, name)
        ok = result.get("success", False)
        return ToolResult(ok, data={
            "name": result.get("name"),
            "path": result.get("path"),
            "model": result.get("model"),
            "error": result.get("error"),
        }, error=result.get("error") if not ok else None)

    def list_music_models(self):
        """List all available music generation models."""
        models = self.music_gen.list_available_models()
        state = self.music_gen.get_state()
        return ToolResult(True, {
            "current_model": state.get("current_model"),
            "available_models": models,
            "count": len(models),
        })

    def select_music_model(self, name_or_path):
        """Switch music generation model by name or path.
        
        Examples:
          - select_music_model("musicgen-medium")  # known model
          - select_music_model("musicgen-large")   # larger model
          - select_music_model("D:/models/mymusic")  # local path
        """
        result = self.music_gen.select_model(name_or_path)
        ok = result.get("success", False)
        state = self.music_gen.get_state()
        return ToolResult(ok, data={
            "model": name_or_path,
            "current_model": state.get("current_model"),
            "loaded": state.get("loaded"),
            "disabled": state.get("disabled"),
        }, error=result.get("error") if not ok else None)

    # ==================== UTILITY TOOLS ====================

    def list_generated_assets(self):
        images = self.image_gen.list_assets()
        music = self.music_gen.list_assets()
        return ToolResult(True, {"images": images, "music": music})

    def get_engine_info(self):
        """Return full engine status with all subsystem states."""
        img_state = self.image_gen.get_state()
        mus_state = self.music_gen.get_state()
        return ToolResult(True, {
            "version": get_config().version,
            "physics": {"enabled": not self.physics._disabled, "initialized": self.physics._initialized},
            "audio": self.audio.get_state() if not self.audio._disabled else {"disabled": True},
            "image_gen": {
                "loaded": img_state.get("loaded"),
                "current_model": img_state.get("current_model"),
                "available_models_count": len(img_state.get("available_models", [])),
            },
            "music_gen": {
                "loaded": mus_state.get("loaded"),
                "current_model": mus_state.get("current_model"),
                "available_models_count": len(mus_state.get("available_models", [])),
            },
            "world": self.world.summary,
            "scene_3d": {"entities": len(self.scene_3d.meshes), "lights": len(self.scene_3d.lights)},
        })

    # Override list_tools to include V2 tools
    def list_tools(self):
        base = super().list_tools().data.get("tools", [])
        v2_tools = [
            {"name": "init_physics", "desc": "Initialize physics engine"},
            {"name": "add_physics_body", "desc": "Add physics body to entity"},
            {"name": "remove_physics_body", "desc": "Remove physics body"},
            {"name": "apply_force", "desc": "Apply force to physics body"},
            {"name": "set_gravity", "desc": "Set world gravity"},
            {"name": "ray_cast", "desc": "Cast ray and find first hit"},
            {"name": "get_physics_info", "desc": "Get physics body info"},
            {"name": "init_audio", "desc": "Initialize audio engine"},
            {"name": "load_sound", "desc": "Register a sound file"},
            {"name": "play_sound", "desc": "Play a sound effect"},
            {"name": "play_music", "desc": "Play background music"},
            {"name": "stop_music", "desc": "Stop background music"},
            {"name": "set_audio_volume", "desc": "Set audio volume levels"},
            {"name": "get_audio_state", "desc": "Get audio engine status"},
            {"name": "set_3d_mesh", "desc": "Set 3D mesh for entity"},
            {"name": "set_3d_transform", "desc": "Set 3D transform for entity"},
            {"name": "add_3d_light", "desc": "Add light to 3D scene"},
            {"name": "set_3d_camera", "desc": "Set 3D camera"},
            {"name": "get_3d_state", "desc": "Get full 3D scene state"},
            {"name": "init_image_gen", "desc": "Initialize image generation"},
            {"name": "generate_image", "desc": "Generate image from prompt"},
            {"name": "generate_texture", "desc": "Generate texture from prompt"},
            {"name": "list_image_models", "desc": "List available image generation models"},
            {"name": "select_image_model", "desc": "Switch image generation model by name or path"},
            {"name": "init_music_gen", "desc": "Initialize music generation"},
            {"name": "generate_music", "desc": "Generate music from description"},
            {"name": "generate_sound_effect", "desc": "Generate SFX from description"},
            {"name": "list_music_models", "desc": "List available music generation models"},
            {"name": "select_music_model", "desc": "Switch music generation model by name or path"},
            {"name": "list_generated_assets", "desc": "List AI-generated assets"},
            {"name": "get_engine_info", "desc": "Get full engine status info"},
        ]
        return ToolResult(True, {"tools": base + v2_tools})