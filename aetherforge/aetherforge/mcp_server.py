"""
AetherForge MCP Server — Direct Engine Access (no Flask dependency).

Modes:
  DIRECT (default): EngineToolsV2 in-process. No Flask needed.
  PROXY (--proxy):  HTTP proxy to Flask server (legacy, shared state).

Usage:
    python -m aetherforge.mcp_server           # direct (recommended)
    python -m aetherforge.mcp_server --proxy    # proxy to Flask
"""
import json
import sys
import os
import asyncio
import traceback

from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult, Resource, TextResourceContents
import mcp.server.stdio
from aetherforge.config import get_config
from aetherforge.tools.network import network_manager

# ── Engine reference (set by main()) ──
_ENGINE = {"world": None, "tools": None, "runtime": None}
_PROXY_BASE = None  # "http://127.0.0.1:7890" when in proxy mode


# ── Tool definitions ──


def _build_tool_defs(eng):
    """从引擎反射构建 MCP Tool 定义，包含参数 schema。"""
    try:
        result = eng.list_tools()
        data = result.to_dict() if hasattr(result, "to_dict") else result
        tool_list = []
        if isinstance(data, dict):
            tool_list = data.get("data", {}).get("tools", [])
            if not tool_list:
                # 尝试直接从引擎的 _tools 字典读取完整信息
                raw_tools = getattr(eng, "_tools", {}) or getattr(eng, "tools", {})
                tool_list = [
                    {
                        "name": name,
                        "desc": getattr(fn, "_tool_desc", "") or fn.__doc__ or "",
                        "schema": getattr(fn, "_tool_schema", {"type": "object", "properties": {}}),
                    }
                    for name, fn in raw_tools.items()
                ]
        elif isinstance(data, list):
            tool_list = data
    except Exception as e:
        print(f"[MCP] Failed to reflect tools: {e}", file=sys.stderr, flush=True)
        tool_list = []

    mcp_tools = []
    for t in tool_list:
        schema = t.get("schema") or t.get("inputSchema", {"type": "object", "properties": {}})
        if isinstance(schema, dict) and "type" not in schema:
            schema["type"] = "object"
        mcp_tools.append(
            Tool(
                name=t.get("name", "unknown"),
                description=t.get("desc", t.get("description", "")),
                inputSchema=schema,
            )
        )
    return mcp_tools


_TOOL_DEF_CACHE = []


def _get_tool_defs():
    """返回引擎初始化后缓存的工具定义。"""
    return list(_TOOL_DEF_CACHE) if _TOOL_DEF_CACHE else []


server = Server("aetherforge-engine")


# ── MCP Handlers (direct mode) ──


@server.list_tools()
async def handle_list_tools():
    tools = _get_tool_defs()
    if not tools:
        print("[MCP] Warning: no tools available - engine may not be initialized", file=sys.stderr, flush=True)
    return tools


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
                available = [t.name for t in _TOOL_DEF_CACHE]
                hint = ""
                if available:
                    hint = f" Available tools: {', '.join(available[:10])}"
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {"success": False, "error": f"Unknown tool: {name}.{hint}"},
                                indent=2,
                                ensure_ascii=False,
                            ),
                        )
                    ]
                )

            result = fn(**args)
            if hasattr(result, "to_dict"):
                result = result.to_dict()
        else:
            result = {
                "success": False,
                "error": "Engine not initialized. Run without --proxy, or start Flask first.",
            }

        text = json.dumps(result, indent=2, ensure_ascii=False)
        return CallToolResult(content=[TextContent(type="text", text=text)])
    except TypeError as te:
        # 参数类型错误 — 给出更友好的提示
        error_msg = str(te)
        if "required positional argument" in error_msg:
            fn = getattr(_ENGINE.get("tools"), name, None)
            if fn:
                import inspect
                sig = inspect.signature(fn)
                params = list(sig.parameters.keys())
                error_msg = f"Missing arguments for '{name}'. Required: {params}"
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"success": False, "error": error_msg},
                        indent=2,
                        ensure_ascii=False,
                    ),
                )
            ]
        )
    except Exception as ex:
        traceback.print_exc()
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"success": False, "error": f"{type(ex).__name__}: {str(ex)}"},
                        indent=2,
                        ensure_ascii=False,
                    ),
                )
            ]
        )


@server.list_resources()
async def handle_list_resources():
    return [
        Resource(
            uri="aetherforge://world/summary",
            name="World Summary",
            mimeType="application/json",
        ),
        Resource(
            uri="aetherforge://world/snapshot",
            name="World Snapshot",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str):
    w = _ENGINE["world"]

    if uri == "aetherforge://world/summary":
        if w:
            data = {"success": True, "data": getattr(w, "summary", {})}
        else:
            data = {"success": False, "error": "Not initialized"}
    elif uri == "aetherforge://world/snapshot":
        if w:
            snap = w.snapshot() if hasattr(w, "snapshot") else w.observe()
            sd = snap.to_dict() if hasattr(snap, "to_dict") else str(snap)
            data = {"success": True, "data": sd}
        else:
            data = {"success": False, "error": "Not initialized"}
    else:
        raise ValueError(f"Unknown resource: {uri}")

    text = json.dumps(data, indent=2, ensure_ascii=False)
    return TextResourceContents(
        uri=uri, mimeType="application/json", text=text
    )


# ── Main ──


def build_direct_engine(checkpoint_interval=60):
    """创建 EngineToolsV2 + Runtime (in-process，不依赖 Flask)。

    Args:
        checkpoint_interval: 自动保存间隔（tick 数），0 表示禁用。
    """
    from aetherforge.core.world_model import WorldModel
    from aetherforge.api.engine_v2 import EngineToolsV2
    from aetherforge.runtime.game_loop import GameRuntime

    wm = WorldModel()
    rt = GameRuntime(wm, checkpoint_interval=checkpoint_interval)
    eng = EngineToolsV2(wm, runtime=rt)
    return wm, eng, rt


async def _init_network():
    """启动时初始化网络检测（非阻塞）。"""
    try:
        result = network_manager.detect(background=False)
        if result.get("success"):
            cur = result.get("current", {})
            sys.stderr.write(
                f"[network] Source: {cur.get('name', '?')} ({cur.get('latency_ms', '?')} ms)\n"
            )
        else:
            sys.stderr.write("[network] No online source. Offline mode.\n")
    except Exception:
        sys.stderr.write("[network] Detection skipped.\n")


def _log_startup_summary(tool_count, errors):
    """打印启动摘要信息。"""
    print(f"  {tool_count} tools from engine reflection, no Flask needed", file=sys.stderr, flush=True)
    if errors:
        for err in errors:
            print(f"  [WARN] {err}", file=sys.stderr, flush=True)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="AetherForge MCP Server")
    parser.add_argument(
        "--proxy",
        action="store_true",
        help="Proxy mode: connect to Flask (deprecated)",
    )
    parser.add_argument(
        "--port", type=int, default=7890, help="Flask port (proxy only)"
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=60,
        help="Auto-save interval in ticks",
    )
    parser.add_argument(
        "--version", action="store_true", help="Show version and exit"
    )
    args = parser.parse_args()

    if args.version:
        print(f"AetherForge MCP Server v{get_config().version}")
        return

    if args.checkpoint_interval < 0:
        args.checkpoint_interval = 0

    if args.proxy:
        print(
            "  [WARN] --proxy mode is deprecated. "
            "Direct mode is now the default and recommended.",
            file=sys.stderr,
            flush=True,
        )
        print(
            "  [WARN] Falling back to direct mode (no Flask needed).",
            file=sys.stderr,
            flush=True,
        )

    # Direct mode (always)
    w, e, r = build_direct_engine(checkpoint_interval=args.checkpoint_interval)
    _ENGINE["world"] = w
    _ENGINE["tools"] = e
    _ENGINE["runtime"] = r

    version = get_config().version
    print(
        f"AetherForge MCP Server v{version} (direct mode)",
        file=sys.stderr,
        flush=True,
    )

    startup_errors = []
    try:
        _TOOL_DEF_CACHE[:] = _build_tool_defs(_ENGINE["tools"])
    except Exception as ex:
        startup_errors.append(f"Tool reflection failed: {ex}")
        _TOOL_DEF_CACHE[:] = []

    _log_startup_summary(len(_TOOL_DEF_CACHE), startup_errors)

    print("  Waiting for MCP client...", file=sys.stderr, flush=True)

    async with mcp.server.stdio.stdio_server() as (rs, ws):
        await server.run(
            rs,
            ws,
            mcp.server.models.InitializationOptions(
                server_name="aetherforge-engine",
                server_version=version,
                capabilities={},
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
