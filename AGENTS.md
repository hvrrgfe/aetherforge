# AetherForge - AGENTS.md

## AI Agent Instructions

You are using **AetherForge**, an AI-native game engine. **AI Agent is the primary user**, humans are supervisors.

### First Principles

1. **Do NOT edit Python files directly.** Use engine tools instead.
2. **Connect via MCP Server** (`python -m aetherforge.mcp_server`) for native tool access.
3. **All operations return JSON** ? parse results, don't grep logs.
4. **Use transactions** ? call `_checkpoint()` before multi-step changes, `rollback()` on failure.
5. **Use semantic types** ? each entity has a `semantic_type`, `description`, `capabilities`.

### Autonomous Work Cycle

```
read_project ? create/modify ? observe ? test ? fix ? commit
```

Use `DevCycle().full_cycle()` for the complete autonomous pipeline.

### Available Tools (49+)

#### Core (always available)
`create_entity`, `modify_entity`, `remove_entity`, `get_entity`, `find_entities`
`create_rule`, `remove_rule`, `create_quest`, `complete_quest_step`
`set_behavior`, `set_weather`, `set_player`, `trigger_event`
`observe`, `commit_change`, `rollback_change`, `read_project`
`set_audio`, `set_art_intent`, `save_project`, `load_project`

#### Physics (requires pymunk)
`init_physics`, `add_physics_body`, `apply_force`, `set_gravity`, `ray_cast`

#### Audio (requires pygame)
`init_audio`, `load_sound`, `play_sound`, `play_music`, `stop_music`, `set_audio_volume`

#### 3D (Three.js in browser)
`set_3d_mesh`, `set_3d_transform`, `add_3d_light`, `set_3d_camera`, `get_3d_state`

#### AI Image Gen (requires torch + diffusers)
`init_image_gen`, `generate_image`, `generate_texture`
Configure model path: config.image_gen.model_path = "/path/to/anything-v5"

#### AI Music Gen (requires torch + audiocraft)
`init_music_gen`, `generate_music`, `generate_sound_effect`

### Demo Scenarios

- **Rainy Station (2D)**: `python -m aetherforge.main --demo`
- **Rainy Station (3D)**: `python -m aetherforge.main --demo-3d`
- **Autonomous Build**: `from aetherforge.autonomous import DevCycle; DevCycle().full_cycle()`

### Entity Structure

Every entity has:
```json
{
  "entity_id": "ent_abc123",
  "semantic_type": "player | npc | locked_door | key_item | building | ...",
  "name": "Human-readable name",
  "description": "What is this, what does it do, why does it exist",
  "capabilities": ["move", "interact", "pick_up"],
  "state": {"health": 100, "inventory": []},
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "relationships": [{"type": "contains", "target": "ent_..."}]
}
```

### Debugging

- `observe()` ? full world snapshot as JSON
- `read_project()` ? summary (entity/rule/quest counts)
- `get_engine_info()` ? all subsystem status
- `list_generated_assets()` ? AI-generated images/music
- World viewer: `http://localhost:7890/`
- 3D viewer: `http://localhost:7890/viewer-3d`

## Project Structure
This project uses a flat structure - the git root is also the project root. No nested directories.
