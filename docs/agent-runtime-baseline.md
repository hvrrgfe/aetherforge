# AetherForge Agent Runtime - Baseline Document

## Repository Information
- **Repository**: hvrrgfe/aetherforge
- **Latest Commit**: 12657c9 fix: add desc/trigger/action aliases and commit_change message param
- **Python**: 3.10.6
- **PyTorch**: 2.13.0+cpu (CUDA unavailable)
- **audiocraft**: 1.3.0

## Current Architecture

### Python Engine (aetherforge/)
| Module | Path | Status |
|--------|------|--------|
| Core World Model | aetherforge/core/world_model.py | Complete |
| Engine Tools (56+) | aetherforge/api/tools.py | Complete |
| Engine Tools V2 | aetherforge/api/engine_v2.py | Complete (extends base) |
| MCP Server | aetherforge/mcp_server.py | Complete |
| Flask Web UI | aetherforge/main.py | Complete |
| CLI | aetherforge/cli.py | Complete |
| Physics | aetherforge/runtime/physics.py | Complete (pymunk) |
| Audio | aetherforge/runtime/audio.py | Complete (pygame) |
| Game Loop | aetherforge/runtime/game_loop.py | Complete |
| 3D Renderer | aetherforge/renderer/__init__.py | Complete (Three.js) |
| Image Generation | aetherforge/ai_engines/image_gen.py | Complete (diffusers) |
| Music Generation | aetherforge/ai_engines/music_gen.py | FIXED (was not loading model) |
| Model Manager | aetherforge/tools/model_manager.py | Complete |
| Config | aetherforge/config.py | Complete |
| Demos | aetherforge/demo/ | Complete (2D + 3D) |

### Java Desktop Editor (src/)
- **Technology**: Java 21 + Swing + FlatLaf + Gson
- **Path**: src/com/aetherforge/AetherForgeStudio.java
- **Status**: Complete (Scene/Entity editor with undo/redo)

## Test Results
- **Security Tests**: 22/22 PASSED
- **Test coverage**: Limited (only test_security.py exists)

## MCP Server
- **Mode**: Direct (in-process, no Flask dependency)
- **Tool Discovery**: Reflection via @tool decorator
- **Tools Count**: 67 (as reported by MCP)
- **Start Command**: python -m aetherforge.mcp_server

## Key Interfaces (Must Not Break)
1. ToolResult(success, data, error)
2. @tool(desc=...) decorator
3. EngineTools(world) - base class
4. EngineToolsV2(world, runtime) - extended class
5. WorldModel - entities, rules, quests, behaviors
6. SemanticEntity - core entity type
7. Rule, Quest, QuestStep, NPCBehavior - core types
8. WorldModel._checkpoint() / commit()
9. observe() - full world snapshot
10. commit_change / rollback_change

## Music Generation Fix (Phase 0)
- **Root Cause**: MusicGenEngine.init() only imported audiocraft but never instantiated model
- **Fix**: Added _ensure_model_loaded() with MusicGen.get_pretrained()
- **Behavior**: Model loads lazily on first generate_music() call
- **select_model()** resets _model to None for lazy reload

## Known Issues
1. CUDA unavailable - all AI runs on CPU (slow)
2. No existing Agent Runtime
3. No Evidence/Transaction/Commit Gate
4. WinUI desktop not started
5. Only 22 security tests exist

## Risk Points
1. WorldModel._checkpoint() uses deque(maxlen=100)
2. No world_revision tracking
3. No permission system for tools
4. All 56+ tools are equally accessible
