"""
AetherForge MCP Server - Proxies to the running AetherForge Flask server.
All 50+ tools available via MCP protocol, sharing same world state as web UI.

Run: python -m aetherforge.mcp_server
Requires: AetherForge Flask server running on http://127.0.0.1:7890
"""
import json, sys, os, asyncio, traceback, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult, Resource, TextResourceContents
import mcp.server.stdio
from aetherforge.config import get_config

API_BASE = "http://127.0.0.1:7890"
server = Server("aetherforge-engine")

def _api_call(tool_name, **kwargs):
    """Call the Flask REST API and return parsed result."""
    data = json.dumps(kwargs).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/api/tools/{tool_name}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except Exception:
            return {"success": False, "error": f"HTTP {e.code}: {body[:200]}"}
    except Exception as ex:
        return {"success": False, "error": str(ex)}

def _api_get(path):
    """GET from Flask API and return parsed JSON."""
    try:
        resp = urllib.request.urlopen(f"{API_BASE}{path}", timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as ex:
        return {"success": False, "error": str(ex)}

# ---- Fetch tool definitions from running server ----
def _fetch_tool_defs():
    result = _api_get("/api/tools")
    if result.get("success"):
        tools_list = result.get("data", {}).get("tools", [])
        defs = []
        for t in tools_list:
            defs.append(Tool(
                name=t["name"],
                description=t.get("desc", ""),
                inputSchema={"type": "object", "properties": {}},
            ))
        return defs
    return []

TOOL_DEFS = _fetch_tool_defs()

# ---- MCP Handlers ----

@server.list_tools()
async def handle_list_tools():
    return TOOL_DEFS

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    try:
        result = _api_call(name, **(arguments or {}))
        text = json.dumps(result, indent=2, ensure_ascii=False)
        return CallToolResult(content=[TextContent(type="text", text=text)])
    except Exception as ex:
        traceback.print_exc()
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"success": False, "error": str(ex)}, indent=2))]
        )

@server.list_resources()
async def handle_list_resources():
    return [
        Resource(uri="aetherforge://world/summary", name="World Summary", mimeType="application/json"),
        Resource(uri="aetherforge://world/snapshot", name="World Snapshot", mimeType="application/json"),
        Resource(uri="aetherforge://world/entities", name="All Entities", mimeType="application/json"),
        Resource(uri="aetherforge://world/rules", name="All Rules", mimeType="application/json"),
        Resource(uri="aetherforge://world/quests", name="All Quests", mimeType="application/json"),
    ]

@server.read_resource()
async def handle_read_resource(uri: str):
    path_map = {
        "aetherforge://world/summary": "/api/summary",
        "aetherforge://world/snapshot": "/api/observe",
        "aetherforge://world/entities": "/api/observe",
        "aetherforge://world/rules": "/api/observe",
        "aetherforge://world/quests": "/api/observe",
    }
    path = path_map.get(uri)
    if not path:
        raise ValueError(f"Unknown resource: {uri}")
    data = _api_get(path)
    text = json.dumps(data, indent=2, ensure_ascii=False)
    return TextResourceContents(uri=uri, mimeType="application/json", text=text)

async def main():
    print("AetherForge MCP Server v2.0.0 (proxy mode) started - waiting for MCP client...", flush=True)
    print(f"  Proxying to Flask server at {API_BASE}", flush=True)
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
