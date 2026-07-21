"""
AetherForge MCP Server — Direct Engine Access (no Flask dependency).

Modes:
  DIRECT (default): EngineToolsV2 in-process. No Flask needed.
  PROXY (--proxy):  HTTP proxy to Flask server (legacy, shared state).

Usage:
    python -m aetherforge.mcp_server           # direct (recommended)
    python -m aetherforge.mcp_server --proxy    # proxy to Flask
"""
import json, sys, os, asyncio, traceback


from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult, Resource, TextResourceContents
import mcp.server.stdio
from aetherforge.config import get_config

# ── Engine reference (set by main()) ──
_ENGINE = {"world": None, "tools": None, "runtime": None}
_PROXY_BASE = None  # "http://127.0.0.1:7890" when in proxy mode


# ── Tool definitions ──
'''
Build MCP Tool definitions from engine reflection.
The engine uses @tool decorators to mark callable tools.
'''

def _build_tool_defs(eng):
    """Build MCP Tool objects from engine reflection."""
    result = eng.list_tools()
    data = result.to_dict() if hasattr(result, 'to_dict') else result
    tool_list = []
    if isinstance(data, dict):
        tool_list = data.get('data', {}).get('tools', [])
    elif isinstance(data, list):
        tool_list = data
    return [
        Tool(name=t['name'], description=t['desc'],
             inputSchema={'type': 'object', 'properties': {}})
        for t in tool_list
    ]


_TOOL_DEF_CACHE = []

def _get_tool_defs():
    """Return cached tool definitions built after engine init."""
    return _TOOL_DEF_CACHE

server = Server("aetherforge-engine")


# ── MCP Handlers (direct mode) ──


@server.list_tools()
async def handle_list_tools():
    return list(_get_tool_defs())  # copy to protect cache


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    try:
        args = arguments or {}
        eng = _ENGINE["tools"]
        rt = _ENGINE["runtime"]

        if eng:
            fn = getattr(eng, name, None)
            if fn is None and rt:
                fn = getattr(rt, name, None)
            if fn is None:
                return CallToolResult(content=[TextContent(type="text", text=json.dumps(
                    {"success": False, "error": f"Unknown tool: {name}"}, indent=2))])
            result = fn(**args)
            if hasattr(result, "to_dict"):
                result = result.to_dict()
        else:
            result = {"success": False, "error": "Engine not initialized. Run without --proxy, or start Flask first."}

        text = json.dumps(result, indent=2, ensure_ascii=False)
        return CallToolResult(content=[TextContent(type="text", text=text)])
    except Exception as ex:
        traceback.print_exc()
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(
            {"success": False, "error": str(ex)}, indent=2))])


@server.list_resources()
async def handle_list_resources():
    return [
        Resource(uri="aetherforge://world/summary", name="World Summary", mimeType="application/json"),
        Resource(uri="aetherforge://world/snapshot", name="World Snapshot", mimeType="application/json"),
    ]


@server.read_resource()
async def handle_read_resource(uri: str):
    w = _ENGINE["world"]

    if uri == "aetherforge://world/summary":
        if w:
            data = {"success": True, "data": w.summary}
        else:
            data = {"success": False, "error": "Not initialized"}
    elif uri == "aetherforge://world/snapshot":
        if w:
            snap = w.snapshot()
            sd = snap.to_dict() if hasattr(snap, "to_dict") else str(snap)
            data = {"success": True, "data": sd}
        else:
            data = {"success": False, "error": "Not initialized"}
    else:
        raise ValueError(f"Unknown resource: {uri}")

    text = json.dumps(data, indent=2, ensure_ascii=False)
    return TextResourceContents(uri=uri, mimeType="application/json", text=text)


# ── Main ──

def build_direct_engine(checkpoint_interval=60):
    """Create EngineToolsV2 + Runtime in-process (no Flask).
    Args:
        checkpoint_interval: auto-save interval in ticks (0 to disable)"""
    from aetherforge.core.world_model import WorldModel
    from aetherforge.api.engine_v2 import EngineToolsV2
    from aetherforge.runtime.game_loop import GameRuntime
    wm = WorldModel()
    rt = GameRuntime(wm, checkpoint_interval=checkpoint_interval)
    eng = EngineToolsV2(wm, runtime=rt)
    return wm, eng, rt


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="AetherForge MCP Server")
    parser.add_argument("--proxy", action="store_true", help="Proxy mode: connect to Flask")
    parser.add_argument("--port", type=int, default=7890, help="Flask port (proxy only)")
    parser.add_argument("--checkpoint-interval", type=int, default=60, help="Auto-save interval in ticks")
    args = parser.parse_args()

    if args.checkpoint_interval < 0:
        args.checkpoint_interval = 0
    if args.proxy:
        print("  [WARN] --proxy mode is deprecated. Direct mode is now the default and recommended.", flush=True)
        print("  [WARN] Falling back to direct mode (no Flask needed).", flush=True)
    # Direct mode (always)
    w, e, r = build_direct_engine(checkpoint_interval=args.checkpoint_interval)
    _ENGINE["world"] = w
    _ENGINE["tools"] = e
    _ENGINE["runtime"] = r
    print(f"AetherForge MCP Server v{get_config().version} (direct mode)", flush=True)
    _TOOL_DEF_CACHE[:] = _build_tool_defs(_ENGINE['tools'])
    print(f"  {len(_TOOL_DEF_CACHE)} tools from engine reflection, no Flask needed", flush=True)

    print("  Waiting for MCP client...", flush=True)
    async with mcp.server.stdio.stdio_server() as (rs, ws):
        await server.run(
            rs, ws,
            mcp.server.models.InitializationOptions(
                server_name="aetherforge-engine",
                server_version=get_config().version,
                capabilities={},
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())