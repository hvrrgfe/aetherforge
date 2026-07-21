# AetherForge Agent Guide

## Project Structure (Python)
- pi/tools.py -- Base EngineTools class. All callable tools use @tool(desc="...") decorator.
- pi/engine_v2.py -- EngineToolsV2 extends base with physics/audio/3D/AI tools. Same decorator pattern.
- mcp_server.py -- MCP server that discovers tools dynamically via _get_tool_defs().
- untime/game_loop.py -- Game loop with auto-checkpoint every 60 ticks.
- core/ -- World model, entities, rules, quests, behaviors.
- i_engines/ -- Image gen, music gen engines.
- enderer/ -- 3D scene graph (SceneGraph3D).
- 	ools/ -- Utility functions (model_manager, etc.).
- 	est/ -- Test suite.

## Adding a New Tool
1. Add the method to EngineTools (base) or EngineToolsV2 (extended).
2. Decorate with @tool(desc="Short description").
3. The list_tools() method uses inspect.getmembers() reflection -- no manual registration needed.
4. If adding to EngineToolsV2, the base class list_tools() auto-discovers inherited + new methods.

## Python File Constraints
- All Python source files must be **pure ASCII** (no Unicode > U+00FF).
- Reason: Windows + Chinese locale causes compile() errors on non-ASCII chars in strings.
- Non-ASCII comments/documentation must be converted to ASCII equivalents.

## Running Tests
`ash
# Unit tests (17)
python -m aetherforge.test.test_runner

# Physics tests (8)
python -m aetherforge.test.test_physics

# Security tests (22)
python -m aetherforge.test.test_security

# Engine module tests (27)
python D:\game\AetherForgeStudio\aetherforge\test\test_engines.py

# CLI+Config tests (9)
python -m aetherforge.test.test_cli_config

# MCP integration tests (11)
python -m aetherforge.test.test_integration_mcp
`

## Environment
- Python 3.10.6 on Windows
- PYTHONPATH: D:\game\AetherForgeStudio\aetherforge;D:\game\AetherForgeStudio
- CWD: D:\game

## File Writing (Windows Encoding)
PowerShell mangling Python strings with quotes. Always write files via Python:
`python
python -c "f=open('path','w',encoding='utf-8').write(content)"
`
Or use PowerShell herestring @" "@ with Set-Content -Encoding UTF8.

## Debug Guide
`ash
# Run MCP server in direct mode (no Flask)
python -m aetherforge.mcp_server

# Run CLI
python -m aetherforge.cli

# Verify tool discovery
python -c "from aetherforge.api.engine_v2 import EngineToolsV2; from aetherforge.core.world_model import WorldModel; e=EngineToolsV2(WorldModel()); r=e.list_tools(); print(len(r.data['tools']), 'tools discovered')"
`

## ToolResult Convention
- All engine tools return ToolResult(success, data, error).
- ToolResult.ok is deprecated; use .success only.
- To dict: esult.to_dict() returns {'success': bool, 'data': dict, 'error': str|None}.
- To JSON string: esult.to_json().

## Tool Discovery Architecture
- EngineTools.__init__ calls self._discover_tools() to build cache.
- EngineToolsV2.__init__ calls self._discover_tools() again after initing V2 subsystems.
- list_tools() returns cached result -- no reflection overhead at call time.
- mcp_server.py populates tool defs eagerly in main() after engine build.
- Adding a new tool: add method + @tool(desc="...") decorator; no manual registration needed.

## Checkpoint System
- GameRuntime(world, checkpoint_interval=N) -- auto-checkpoints every N ticks.
- Default: 60 ticks.
- Set checkpoint_interval=0 to disable auto-checkpoint.

## Contribution Notes
- Keep all Python source files pure ASCII (no Unicode > U+00FF).
- Test-driven: run full suite before submitting changes.
- Do not add sys.path.insert hacks; the package uses proper import paths.
- Do not add new hardcoded registries; use the @tool decorator pattern.
