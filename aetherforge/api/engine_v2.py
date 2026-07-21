"""EngineTools V2 - extends EngineTools with physics, audio, 3D, and AI tools.

All tools return ToolResult for consistent MCP/API access.
"""
import sys, os, json
from aetherforge.api.tools import EngineTools, ToolResult, tool
from typing import Optional, Any
from aetherforge.runtime.physics import PhysicsEngine
from aetherforge.runtime.audio import AudioEngine
from aetherforge.renderer import SceneGraph3D, MeshData, Transform3D, Vector3, Light3D, Camera3D
from aetherforge.ai_engines.image_gen import ImageGenEngine
from aetherforge.ai_engines.music_gen import MusicGenEngine
from aetherforge.config import get_config
from aetherforge.tools.model_manager import model_mgr


class EngineToolsV2(EngineTools):
    """Extended engine tools with Physics, Audio, 3D, and AI capabilities."""

    def __init__(self, world: Any, runtime: Optional[Any] = None) -> None:
        super().__init__(world)
        self.runtime = runtime
        self.physics = PhysicsEngine(world)
        self.audio = AudioEngine()
        self.scene_3d = SceneGraph3D(world)
        self.image_gen = ImageGenEngine()
        self.music_gen = MusicGenEngine()
        self._discover_tools()  # rediscover V2 tools

    # ==================== PHYSICS TOOLS ====================

    @tool(desc="Initialize physics engine (pymunk)")
    def init_physics(self):
        try:
            self.physics.init()
            return ToolResult(True, {"initialized": not self.physics._disabled})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Add physics body to entity")
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

    @tool(desc="Remove physics body")
    def remove_physics_body(self, entity_id):
        ok = self.physics.remove_body(entity_id)
        return ToolResult(ok, {"entity_id": entity_id}) if ok else ToolResult(False, error=f"Body {entity_id} not found")

    @tool(desc="Apply force to physics body")
    def apply_force(self, entity_id, fx=0.0, fy=0.0):
        ok = self.physics.apply_force(entity_id, fx, fy)
        return ToolResult(True, {"entity_id": entity_id, "force": {"x": fx, "y": fy}}) if ok else ToolResult(False, error="Body not found")

    @tool(desc="Set gravity vector")
    def set_gravity(self, gx=0.0, gy=980.0):
        ok = self.physics.set_gravity(gx, gy)
        return ToolResult(True, {"gravity": {"x": gx, "y": gy}})

    @tool(desc="Cast ray and return first hit")
    def ray_cast(self, start_x, start_y, end_x, end_y):
        hit_id = self.physics.ray_cast(start_x, start_y, end_x, end_y)
        return ToolResult(True, {"hit_entity_id": hit_id, "start": {"x": start_x, "y": start_y}, "end": {"x": end_x, "y": end_y}})

    @tool(desc="Get physics body info")
    def get_physics_info(self, entity_id):
        info = self.physics.get_body_info(entity_id)
        if info:
            return ToolResult(True, info)
        return ToolResult(False, error=f"No physics body for {entity_id}")

    # ==================== AUDIO TOOLS ====================

    @tool(desc="Initialize audio engine (pygame)")
    def init_audio(self):
        try:
            self.audio.init()
            return ToolResult(True, {"initialized": not self.audio._disabled})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Load sound file")
    def load_sound(self, name, file_path):
        ok = self.audio.load_sound(name, file_path)
        return ToolResult(True, {"name": name, "path": file_path}) if ok else ToolResult(False, error=f"Failed to load sound: {name}")

    @tool(desc="Play loaded sound")
    def play_sound(self, name, volume=1.0, loops=0, pan=0.0):
        result = self.audio.play_sound(name, volume, loops, pan)
        return ToolResult(result.get("success", False), data=result)

    @tool(desc="Play background music")
    def play_music(self, name, file_path=None, volume=None, loop=True, fade_ms=0):
        result = self.audio.play_music(name, file_path, volume, loop, fade_ms)
        return ToolResult(result.get("success", False), data=result)

    @tool(desc="Stop background music")
    def stop_music(self, fade_ms=0):
        result = self.audio.stop_music(fade_ms)
        return ToolResult(result.get("success", False), data=result)

    @tool(desc="Set master volume")
    def set_audio_volume(self, master=None, music=None, sfx=None):
        if master is not None:
            self.audio.set_master_volume(master)
        if music is not None:
            self.audio.set_music_volume(music)
        if sfx is not None:
            self.audio.set_sfx_volume(sfx)
        return ToolResult(True, {"master": self.audio._volume, "music": self.audio._music_volume, "sfx": self.audio._sfx_volume})

    @tool(desc="Get audio engine state")
    def get_audio_state(self):
        return ToolResult(True, self.audio.get_state())

    # ==================== 3D TOOLS ====================

    @tool(desc="Set 3D mesh for entity")
    def set_3d_mesh(self, entity_id, geometry="box", color="#888888",
                     texture="", emissive="#000000", metalness=0.0,
                     roughness=0.8, transparent=False, opacity=1.0,
                     wireframe=False):
        md = MeshData(geometry=geometry, color=color, texture=texture,
                      emissive=emissive, metalness=metalness, roughness=roughness,
                      transparent=transparent, opacity=opacity, wireframe=wireframe)
        self.scene_3d.set_mesh(entity_id, md)
        return ToolResult(True, {"entity_id": entity_id, "mesh": md.to_dict()})

    @tool(desc="Set 3D transform")
    def set_3d_transform(self, entity_id, x=0.0, y=0.0, z=0.0,
                          rx=0.0, ry=0.0, rz=0.0, sx=1.0, sy=1.0, sz=1.0):
        tf = Transform3D(position=Vector3(x, y, z),
                         rotation=Vector3(rx, ry, rz),
                         scale=Vector3(sx, sy, sz))
        self.scene_3d.set_transform(entity_id, tf)
        return ToolResult(True, {"entity_id": entity_id, "transform": tf.to_dict()})

    @tool(desc="Add 3D light source")
    def add_3d_light(self, light_type="directional", color="#ffffff",
                      intensity=1.0, px=0.0, py=10.0, pz=10.0, shadow=False):
        light = Light3D(light_type=light_type, color=color, intensity=intensity,
                        position=Vector3(px, py, pz), shadow=shadow)
        idx = self.scene_3d.add_light(light)
        return ToolResult(True, {"light_index": idx, "light": light.to_dict()})

    @tool(desc="Set 3D camera position/target")
    def set_3d_camera(self, px=0.0, py=0.0, pz=10.0, tx=0.0, ty=0.0, tz=0.0,
                       fov=60.0, orthographic=False):
        cam = Camera3D(position=Vector3(px, py, pz), target=Vector3(tx, ty, tz),
                       fov=fov, orthographic=orthographic)
        self.scene_3d.set_camera(cam)
        return ToolResult(True, {"camera": cam.to_dict()})

    @tool(desc="Get full 3D scene state")
    def get_3d_state(self):
        state = self.scene_3d.get_3d_state()
        state["tick"] = self.world.tick
        state["game_time"] = self.world.game_time
        return ToolResult(True, state)

    # ==================== AI IMAGE GEN TOOLS ====================

    @tool(desc="Initialize AI image generation (diffusers)")
    def init_image_gen(self):
        try:
            ok = self.image_gen.init()
            return ToolResult(True, {"ready": ok, "state": self.image_gen.get_state()})
        except Exception as ex:
            return ToolResult(True, {"ready": False, "error": str(ex)})

    @tool(desc="Generate image from prompt")
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

    @tool(desc="Generate texture for entity")
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

    @tool(desc="List available image models")
    def list_image_models(self):
        """List all available image generation models (local + HF cache + known)."""
        models = self.image_gen.list_available_models()
        state = self.image_gen.get_state()
        return ToolResult(True, {
            "current_model": state.get("current_model"),
            "available_models": models,
            "count": len(models),
        })

    @tool(desc="Select active image model")
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

    @tool(desc="Initialize AI music generation (audiocraft)")
    def init_music_gen(self):
        try:
            ok = self.music_gen.init()
            return ToolResult(True, {"ready": ok, "state": self.music_gen.get_state()})
        except Exception as ex:
            return ToolResult(True, {"ready": False, "error": str(ex)})

    @tool(desc="Generate music from prompt")
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

    @tool(desc="Generate sound effect")
    def generate_sound_effect(self, description, duration=2.0, name=None):
        result = self.music_gen.generate_sound_effect(description, duration, name)
        ok = result.get("success", False)
        return ToolResult(ok, data={
            "name": result.get("name"),
            "path": result.get("path"),
            "model": result.get("model"),
            "error": result.get("error"),
        }, error=result.get("error") if not ok else None)

    @tool(desc="List available music models")
    def list_music_models(self):
        """List all available music generation models."""
        models = self.music_gen.list_available_models()
        state = self.music_gen.get_state()
        return ToolResult(True, {
            "current_model": state.get("current_model"),
            "available_models": models,
            "count": len(models),
        })

    @tool(desc="Select active music model")
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

    # === RUNTIME TOOLS ===

    @tool(desc="Advance game simulation by one frame")
    def tick(self, dt=0.016):
        if self.runtime:
            self.runtime.tick(dt)
            return ToolResult(True, {"tick": self.world.tick})
        return ToolResult(False, error="Runtime not initialized")

    @tool(desc="Set player input state")
    def set_player_input(self, up=False, down=False, left=False, right=False):
        if self.runtime:
            self.runtime.set_player_input(up=up, down=down, left=left, right=right)
            return ToolResult(True, {})
        return ToolResult(False, error="Runtime not initialized")

    @tool(desc="Player interacts with entities in range")
    def player_interact(self):
        if self.runtime:
            r = self.runtime.player_interact()
            return ToolResult(r.get("success", False), data=r)
        return ToolResult(False, error="Runtime not initialized")

    @tool(desc="Execute a single game step")
    def step(self):
        if self.runtime:
            self.runtime.tick(1.0 / 60.0)
            return ToolResult(True, {"tick": self.world.tick})
        return ToolResult(False, error="Runtime not initialized")

    @tool(desc="Pause game simulation")
    def pause(self):
        if self.runtime:
            self.runtime.pause()
            return ToolResult(True, {})
        return ToolResult(False, error="Runtime not initialized")

    @tool(desc="Resume game simulation")
    def resume(self):
        if self.runtime:
            self.runtime.resume()
            return ToolResult(True, {})
        return ToolResult(False, error="Runtime not initialized")

    @tool(desc="Set simulation speed multiplier")
    def set_time_scale(self, scale=1.0):
        if self.runtime:
            self.runtime.set_time_scale(scale)
            return ToolResult(True, {"time_scale": scale})
        return ToolResult(False, error="Runtime not initialized")

    @tool(desc="Quick-modify entity without validation")
    def modify_entity_quick(self, entity_id="", changes=None):
        if not entity_id:
            return ToolResult(False, error="entity_id required")
        changes = changes or {}
        ok = self.world.quick_modify_entity(entity_id, changes)
        return ToolResult(ok, {"entity_id": entity_id})

    @tool(desc="Quick-remove entity without validation")
    def remove_entity_quick(self, entity_id=""):
        if not entity_id:
            return ToolResult(False, error="entity_id required")
        ok = self.world.quick_remove_entity(entity_id)
        return ToolResult(ok, {"entity_id": entity_id})

    @tool(desc="List all AI-generated assets")
    def list_generated_assets(self):
        images = self.image_gen.list_assets()
        music = self.music_gen.list_assets()
        return ToolResult(True, {"images": images, "music": music})

    @tool(desc="Get all subsystem status")
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
    # ==================== AGENT RUNTIME TOOLS ====================
    # High-level tools for the Agent Runtime.
    # External models should use these instead of low-level tools.

    def _get_orchestrator(self):
        if not hasattr(self, '_agent_orch'):
            from aetherforge.agents.orchestrator import AgentOrchestrator
            from aetherforge.agents.state import AgentStateManager
            from aetherforge.agents.policies import AgentPolicy, TokenBudget
            from aetherforge.validation.evidence import EvidenceStore
            from aetherforge.validation.commit_gate import CommitGate, GatePolicy
            from aetherforge.agents.gateway import ToolGateway
            from aetherforge.runtime.permissions import PermissionManager
            sm = AgentStateManager()
            es = EvidenceStore()
            cg = CommitGate(GatePolicy.NORMAL)
            gw = ToolGateway(self, evidence_store=es)
            self._agent_orch = AgentOrchestrator(
                self.world, gw, es, cg, sm,
                policy=AgentPolicy(token_budget=TokenBudget(max_tokens=4000))
            )
            self._agent_evidence = es
            self._agent_gateway = gw
        return self._agent_orch

    @tool(desc="Start a new Agent Runtime task with a natural language goal")
    def agent_start_task(self, goal, constraints=None, approval_mode="high_risk"):
        """Start an agent task. Returns task_id and status."""
        try:
            orch = self._get_orchestrator()
            result = orch.start_task(goal, constraints, approval_mode)
            return ToolResult(True, data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get current status of an agent task")
    def agent_get_status(self, task_id):
        """Get task status including phase, progress, and check counts."""
        try:
            orch = self._get_orchestrator()
            result = orch.get_status(task_id)
            if result:
                return ToolResult(True, data=result)
            return ToolResult(False, error=f"Task {task_id} not found")
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get comprehensive report for an agent task")
    def agent_get_report(self, task_id):
        """Get comprehensive report including evidence, transactions, and checks."""
        try:
            orch = self._get_orchestrator()
            result = orch.get_report(task_id)
            return ToolResult(True, data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get evidence chain for an agent task")
    def agent_get_evidence(self, task_id):
        """Get all evidence collected during a task."""
        try:
            orch = self._get_orchestrator()
            result = orch.get_evidence(task_id)
            return ToolResult(True, data={"evidence": result, "count": len(result)})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Request human approval for a blocked task")
    def agent_request_approval(self, task_id, message=""):
        """Request human approval when task is blocked."""
        try:
            orch = self._get_orchestrator()
            result = orch.request_approval(task_id, message)
            return ToolResult(True, data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Commit an agent task transaction")
    def agent_commit(self, task_id, committer="agent"):
        """Commit the active transaction for a task through the Commit Gate."""
        try:
            orch = self._get_orchestrator()
            result = orch.commit_task(task_id, committer)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Rollback an agent task transaction")
    def agent_rollback(self, task_id):
        """Rollback the active transaction for a task."""
        try:
            orch = self._get_orchestrator()
            result = orch.rollback_task(task_id)
            return ToolResult(True, data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Run a full agent cycle (explore-plan-build-verify-review-commit)")
    def agent_run_full(self, goal, constraints=None):
        """Start and run a complete agent workflow for a goal."""
        try:
            orch = self._get_orchestrator()
            start = orch.start_task(goal, constraints)
            task_id = start.get("task_id", "")
            result = orch.run_full_cycle(task_id)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Run agent workflow with auto-repair loop")
    def agent_run_with_repair(self, goal, constraints=None, max_attempts=3):
        """Start and run agent workflow with automatic repair on failure."""
        try:
            orch = self._get_orchestrator()
            start = orch.start_task(goal, constraints)
            task_id = start.get("task_id", "")
            result = orch.run_with_repair(task_id, max_attempts)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Configure Model Router settings (endpoint, api_key, model)")
    def agent_configure_router(self, endpoint="", api_key="", model_name="", max_tokens=0):
        """Configure the Model Router connection settings."""
        from aetherforge.config import get_config, save_config
        cfg = get_config()
        if endpoint:
            cfg.agent.endpoint = endpoint.rstrip("/")
        if api_key:
            cfg.agent.api_key = api_key
        if model_name:
            cfg.agent.model_name = model_name
        if max_tokens > 0:
            cfg.agent.max_tokens_per_task = max_tokens
        cfg.agent.enabled = True
        path = save_config(cfg)
        return ToolResult(True, data={
            "status": "saved",
            "config_file": path,
            "endpoint": cfg.agent.endpoint,
            "model": cfg.agent.model_name,
        })

    @tool(desc="Show current Model Router configuration")
    def agent_show_router_config(self):
        """Display the current Model Router configuration (masking api_key)."""
        from aetherforge.config import get_config
        cfg = get_config().agent
        key_masked = (cfg.api_key[:8] + "..." + cfg.api_key[-4:]) if len(cfg.api_key) > 12 else ("***" if cfg.api_key else "")
        return ToolResult(True, data={
            "enabled": cfg.enabled,
            "endpoint": cfg.endpoint,
            "api_key_masked": key_masked,
            "model_name": cfg.model_name,
            "max_tokens_per_task": cfg.max_tokens_per_task,
            "policy": cfg.default_policy,
            "approval_mode": cfg.approval_mode,
        })


    @tool(desc="Get world summary (low token cost)")
    def observe_summary(self):
        """Return a compact world summary with entity/rule/quest counts."""
        try:
            w = self.world
            summary = getattr(w, "summary", {})
            return ToolResult(True, data=summary)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get world changes since a given revision")
    def observe_changes(self, since_revision=0):
        """Return delta changes since the given revision."""
        try:
            orch = self._get_orchestrator()
            snapshots = getattr(orch, "_snapshots", None)
            if not snapshots:
                return ToolResult(False, error="No snapshot manager available")
            latest = snapshots.get_latest()
            if not latest:
                return ToolResult(True, data={"changes": [], "message": "No snapshots yet"})
            before = snapshots.get(since_revision) if since_revision > 0 else snapshots.get_before(latest.revision)
            if not before:
                return ToolResult(True, data={"changes": [], "message": f"No snapshot at revision {since_revision}"})
            diff = snapshots.diff(before.revision, latest.revision)
            return ToolResult(True, data={"changes": diff, "current_revision": latest.revision})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get detailed entity data by id")
    def observe_entity(self, entity_id=""):
        """Return detailed data for a single entity."""
        try:
            if not entity_id:
                return ToolResult(False, error="entity_id required")
            w = self.world
            entities = getattr(w, "entities", {})
            entity = entities.get(entity_id) if isinstance(entities, dict) else None
            if not entity:
                return ToolResult(False, error=f"Entity {entity_id} not found")
            if hasattr(entity, "to_dict"):
                data = entity.to_dict()
            elif isinstance(entity, dict):
                data = dict(entity)
            else:
                data = str(entity)
            return ToolResult(True, data={"entity_id": entity_id, "data": data})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Apply a batch world patch (atomic)")
    def apply_world_patch(self, patch_json=""):
        """Apply multiple operations atomically within a transaction.
        Format: {"transaction_id": "...", "operations": [{"op": "...", "data": {...}}, ...]}
        Supported ops: create_entity, modify_entity, remove_entity
        Max 20 operations per patch.
        """
        try:
            import json
            patch = json.loads(patch_json) if isinstance(patch_json, str) else patch_json
            ops = patch.get("operations", [])
            if len(ops) > 20:
                return ToolResult(False, error=f"Too many operations: {len(ops)} (max 20)")
            tx_id = patch.get("transaction_id", "")
            w = self.world
            results = []
            all_ok = True
            # Take checkpoint before any operations for atomic rollback
            has_checkpoint = hasattr(w, "_checkpoint")
            if has_checkpoint:
                w._checkpoint()
            for op in ops:
                op_type = op.get("op", "")
                data = op.get("data", {})
                try:
                    if op_type == "create_entity":
                        from aetherforge.core import SemanticEntity
                        e = SemanticEntity.from_dict(data) if isinstance(data, dict) else data
                        eid = getattr(w, "quick_create_entity", w.create_entity)(e)
                        results.append({"op": op_type, "id": eid, "success": True})
                    elif op_type == "modify_entity":
                        eid = data.pop("entity_id", "")
                        ok = getattr(w, "quick_modify_entity", w.modify_entity)(eid, data)
                        results.append({"op": op_type, "id": eid, "success": bool(ok)})
                        if not ok:
                            all_ok = False
                            break
                    elif op_type == "remove_entity":
                        eid = data.get("entity_id", data.get("id", ""))
                        ok = getattr(w, "quick_remove_entity", w.remove_entity)(eid)
                        results.append({"op": op_type, "id": eid, "success": bool(ok)})
                        if not ok:
                            all_ok = False
                            break
                    else:
                        results.append({"op": op_type, "success": False, "error": f"Unknown op: {op_type}"})
                        all_ok = False
                        break
                except Exception as e:
                    results.append({"op": op_type, "success": False, "error": str(e)})
                    all_ok = False
                    break
            # Atomic rollback on failure
            if not all_ok and has_checkpoint:
                w.rollback()
                for r in results:
                    r["rolled_back"] = True
            return ToolResult(all_ok, data={"operations": results, "transaction_id": tx_id, "atomic": True})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Diff two world revisions")
    def diff_world(self, revision_a=0, revision_b=0):
        """Show structural diff between two world revisions."""
        try:
            if revision_a <= 0 or revision_b <= 0:
                return ToolResult(False, error="Both revision_a and revision_b required")
            orch = self._get_orchestrator()
            snapshots = getattr(orch, "_snapshots", None)
            if not snapshots:
                return ToolResult(False, error="No snapshot manager")
            result = snapshots.diff(revision_a, revision_b)
            if result is None:
                return ToolResult(False, error=f"Snapshots for {revision_a} or {revision_b} not found")
            return ToolResult(True, data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Submit a human suggestion")
    def agent_submit_suggestion(self, suggestion_json=""):
        """Submit a structured human suggestion.
        Format: {"target": {"type": "scene", "id": "..."}, "content": "...", "intent": "..."}
        """
        try:
            import json
            from aetherforge.agents.suggestions import SuggestionManager
            sug = json.loads(suggestion_json) if isinstance(suggestion_json, str) else suggestion_json
            mgr = SuggestionManager()
            sug_obj = mgr.create_suggestion(
                author="user",
                target=sug.get("target", {}),
                content=sug.get("content", ""),
                intent=sug.get("intent", ""),
                constraints=sug.get("constraints", []),
            )
            candidates = mgr.generate_candidates(sug_obj) if sug.get("generate_candidates", False) else []
            return ToolResult(True, data={
                "suggestion_id": sug_obj.id,
                "status": sug_obj.status,
                "candidates": [c.to_dict() for c in candidates] if candidates else [],
            })
        except Exception as ex:
            return ToolResult(False, error=str(ex))


    @tool(desc="Search models from Hugging Face by type and query")
    def search_models(self, query="", model_type="", limit=30):
        """Search for AI models on Hugging Face. model_type: image/music/audio"""
        try:
            from aetherforge.tools.model_manager import model_mgr
            result = model_mgr.search_online_models(query, model_type, limit)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="List all known and locally downloaded models")
    def list_all_models(self, model_type=""):
        """List all models (local + known registry), optionally filtered by type."""
        try:
            from aetherforge.tools.model_manager import model_mgr
            results = model_mgr.list_all_models(model_type)
            return ToolResult(True, data={"count": len(results), "models": results})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Download a model from Hugging Face in background")
    def download_selected_model(self, model_id=""):
        """Start downloading a model in background thread."""
        try:
            if not model_id:
                return ToolResult(False, error="model_id required")
            from aetherforge.tools.model_manager import model_mgr
            result = model_mgr.download_selected_model(model_id)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get current model download progress")
    def get_model_downloads(self):
        """Get progress for all active model downloads."""
        try:
            from aetherforge.tools.model_manager import model_mgr
            return ToolResult(True, data={"downloads": model_mgr.get_model_downloads()})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Select a downloaded model for generation")
    def select_generated_model(self, model_type="", model_id=""):
        """Select which model to use for image/music/audio generation."""
        try:
            if not model_type or not model_id:
                return ToolResult(False, error="model_type and model_id required")
            from aetherforge.tools.model_manager import model_mgr
            result = model_mgr.select_generated_model(model_type, model_id)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Delete a downloaded model")
    def delete_model(self, model_id=""):
        """Delete a locally downloaded model."""
        try:
            if not model_id:
                return ToolResult(False, error="model_id required")
            from aetherforge.tools.model_manager import model_mgr
            result = model_mgr.delete_model(model_id)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get detailed info about a specific model")
    def model_info(self, model_id=""):
        """Get detailed info for a model by model_id."""
        try:
            if not model_id:
                return ToolResult(False, error="model_id required")
            from aetherforge.tools.model_manager import model_mgr
            result = model_mgr.model_info(model_id)
            return ToolResult(result.get("success", False), data=result)
        except Exception as ex:
            return ToolResult(False, error=str(ex))


    @tool(desc="Detect network and select fastest AI model source")
    def detect_model_network(self, refresh=True):
        """Test all configured model sources and select the fastest available one."""
        try:
            from aetherforge.tools.network import network_manager
            result = network_manager.detect(background=False)
            return ToolResult(result.get("success", False), data=result,
                              error=result.get("error", ""))
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Get current AI model source and network status")
    def get_model_network_state(self):
        """Get current network state, active source, and operation mode."""
        try:
            from aetherforge.tools.network import network_manager
            return ToolResult(True, data=network_manager.state())
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Manually switch AI model source by endpoint URL")
    def switch_model_source(self, endpoint=""):
        """Switch to a configured model source by its endpoint URL.
        Example: https://hf-mirror.com or https://huggingface.co
        """
        try:
            if not endpoint:
                return ToolResult(False, error="endpoint required")
            from aetherforge.tools.network import network_manager
            result = network_manager.switch_source(endpoint)
            return ToolResult(result.get("success", False), data=result,
                              error=result.get("error", ""))
        except Exception as ex:
            return ToolResult(False, error=str(ex))
