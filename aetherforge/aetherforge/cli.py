"""AetherForge CLI - AI-native game engine command line interface.

Provides direct CLI access to all engine tools for both AI and human users.
"""
from __future__ import annotations
import sys
import json
import argparse

from aetherforge.core.world_model import WorldModel
from aetherforge.api.engine_v2 import EngineToolsV2 as EngineTools


def main():
    parser = argparse.ArgumentParser(description="AetherForge - AI-Native Game Engine")
    parser.add_argument("--server", action="store_true", help="Start the API server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (use --allow-external for 0.0.0.0)")
    parser.add_argument("--allow-external", action="store_true", help="Allow binding to 0.0.0.0 (WARNING: no auth)")
    parser.add_argument("--port", type=int, default=7890, help="Server port")
    # (demo flag removed)
    parser.add_argument("--project", type=str, help="Load a project file")
    parser.add_argument("--tool", type=str, help="Run a specific tool")
    parser.add_argument("--params", type=str, default="{}", help="JSON parameters for tool")
    parser.add_argument("--observe", action="store_true", help="Print world snapshot")

    args = parser.parse_args()

    # Initialize world
    world = WorldModel()
    tools = EngineTools(world)

    # Load project if specified
    if args.project:
        try:
            tools.load_project(args.project)
            print(f"Loaded project: {args.project}")
        except Exception as e:
            print(f"Error loading project: {e}")
            sys.exit(1)

    # (demo loading removed - blank engine)
        print("Loaded Rainy Station demo project.")

    # Run a specific tool
    if args.tool:
        params = json.loads(args.params) if isinstance(args.params, str) else args.params
        func = getattr(tools, args.tool, None)
        if not func:
            print(f"Unknown tool: {args.tool}")
            print("Available tools: " + str([t['name'] for t in tools.list_tools().data['tools']]))
            sys.exit(1)
        result = func(**params)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        sys.exit(0)

    # Observe world state
    if args.observe:
        print(world.to_json())
        sys.exit(0)

    # Start server
    if args.server:
        if args.host in ("0.0.0.0", "::") and not args.allow_external:
            print("[SECURITY] Refusing to bind to %s. Use --allow-external to override." % args.host)
            sys.exit(1)
        from aetherforge.api.server import run_server
        run_server(host=args.host, port=args.port)
        return

    # Interactive mode
    print("AetherForge AI-Native Game Engine")
    print("Type 'help' for commands, 'quit' to exit.")
    print()

    while True:
        try:
            line = input("aether> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line == "quit":
            break
        if line == "help":
            print("  tool <name> [json_params]  - Call a tool")
            print("  models                   - List all available models")
            print("  download <model>         - Download a model (background)")
            print("  delete <model>           - Delete a downloaded model")
            print("  dl-status                - Check download progress")
            print("  observe                   - Print world snapshot")
            print("  summary                   - Print world summary")
            print("  save <path>               - Save project")
            print("  load <path>               - Load project")
            print("  server                    - Start API server")
            print("  help                      - This help")
            print("  quit                      - Exit")
            continue

        parts = line.split(maxsplit=2)
        cmd = parts[0]

        if cmd == "observe":
            print(world.to_json())
        elif cmd == "summary":
            print(json.dumps(world.summary, indent=2, ensure_ascii=False))
        elif cmd == "save" and len(parts) >= 2:
            tools.save_project(parts[1])
            print(f"Saved to {parts[1]}")
        elif cmd == "load" and len(parts) >= 2:
            tools.load_project(parts[1])
            print(f"Loaded from {parts[1]}")
        elif cmd == "models":
            from aetherforge.tools.model_manager import model_mgr
            models = model_mgr.list_models()
            print("%-20s %-12s %-10s %s" % ("Name", "Type", "Status", "Description"))
            print("-" * 80)
            for m in models:
                print("%-20s %-12s %-10s %s" % (m["name"], m["model_type"], m["status"], m["desc"][:35]))
        elif cmd == "download" and len(parts) >= 2:
            from aetherforge.tools.model_manager import model_mgr
            r = model_mgr.download(parts[1])
            print(r.get("message", str(r)))
        elif cmd == "delete" and len(parts) >= 2:
            from aetherforge.tools.model_manager import model_mgr
            r = model_mgr.delete_model(parts[1])
            print(r.get("message", str(r)))
        elif cmd == "dl-status":
            from aetherforge.tools.model_manager import model_mgr
            dl = model_mgr.download_progress()
            if not dl:
                print("No active downloads")
            for d in dl:
                print("%s: %.1f%% (%s)" % (d["name"], d["progress"], d["status"]))
        elif cmd == "server":
            from aetherforge.api.server import run_server
            run_server()
        elif cmd == "tool" and len(parts) >= 2:
            tool_name = parts[1]
            params = {}
            if len(parts) >= 3:
                try:
                    params = json.loads(parts[2])
                except json.JSONDecodeError:
                    print("Invalid JSON params")
                    continue
            func = getattr(tools, tool_name, None)
            if not func:
                print(f"Unknown tool: {tool_name}")
                continue
            result = func(**params)
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()

