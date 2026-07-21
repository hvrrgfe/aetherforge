"""API Routes Blueprint — 从 main.py 提取的所有 API 路由。

所有路由通过 current_app.config["AETHERFORGE_SERVER"] 访问引擎实例。
"""
import os
import json
import secrets

from flask import Blueprint, request, jsonify, current_app, send_from_directory

from aetherforge.api.tools import ToolResult

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _get_server():
    """获取当前应用的 AetherForgeServer 实例"""
    return current_app.config["AETHERFORGE_SERVER"]


def _check_auth():
    """API Token 认证检查"""
    server = _get_server()
    token = server._api_token
    if token is None:
        return None
    auth = request.headers.get("Authorization", "")
    if auth == f"Bearer {token}":
        return None
    return jsonify(ToolResult(False, error="Unauthorized: provide Authorization: Bearer <token>").to_dict()), 401


def _call_fn(tool_name, data):
    """统一的工具调用路由"""
    server = _get_server()
    world = server.world
    tools = server.tools
    runtime = server.runtime

    if not isinstance(tool_name, str) or not tool_name.isidentifier():
        return ToolResult(False, error="Invalid tool name")

    fn = getattr(tools, tool_name, None)
    if fn:
        return fn(**data)

    if tool_name in ("save_project", "load_project"):
        from aetherforge.tools import validate_project_path as _vpp
        ok, err = _vpp(data.get("path", ""))
        if not ok:
            return ToolResult(False, error=err)

    if tool_name == "tick":
        runtime.tick(data.get("dt", 1.0 / 60.0))
        return ToolResult(True, {"tick": world.tick})

    if tool_name == "set_player_input":
        runtime.set_player_input(**{k: data.get(k, False) for k in ["up", "down", "left", "right"]})
        return ToolResult(True, {})

    if tool_name == "player_interact":
        result = runtime.player_interact()
        return ToolResult(result.get("success", False), data=result)

    if tool_name == "step":
        runtime.tick(1.0 / 60.0)
        return ToolResult(True, {"tick": world.tick})

    if tool_name == "pause":
        runtime.pause()
        return ToolResult(True, {})

    if tool_name == "resume":
        runtime.resume()
        return ToolResult(True, {})

    if tool_name == "set_time_scale":
        runtime.set_time_scale(data.get("scale", 1.0))
        return ToolResult(True, {})

    if tool_name == "modify_entity_quick":
        ok = world.quick_modify_entity(data.get("entity_id", ""), data.get("changes", {}))
        return ToolResult(ok, {})

    if tool_name == "remove_entity_quick":
        ok = world.quick_remove_entity(data.get("entity_id", ""))
        return ToolResult(ok, {})

    return ToolResult(False, error=f"Unknown tool: {tool_name}")


def _build_game_state():
    """构建游戏状态字典"""
    server = _get_server()
    world = server.world
    entities = []
    for eid, e in world.entities.items():
        pos = e.position if hasattr(e, "position") else {}
        viz = e.visual if hasattr(e, "visual") else {}
        sz = e.size if hasattr(e, "size") else {}
        entities.append({
            "id": eid,
            "name": e.name if hasattr(e, "name") else "",
            "type": e.semantic_type if hasattr(e, "semantic_type") else "",
            "x": pos.get("x", 0), "y": pos.get("y", 0),
            "width": sz.get("width", 32), "height": sz.get("height", 32),
            "color": viz.get("color", "#888"),
            "shape": viz.get("shape", "rectangle"),
            "state": e.state if hasattr(e, "state") else {},
            "is_player": eid == world.player_entity_id,
        })
    return {
        "tick": world.tick,
        "weather": world.weather,
        "game_time": world.game_time,
        "camera": world.camera,
        "player_entity_id": world.player_entity_id,
        "entities": entities,
        "revision": world.revision,
    }


# ════════════════════════════════════════════
#  API 路由
# ════════════════════════════════════════════


@api_bp.route("/tools/<tool_name>", methods=["POST"])
def call_tool(tool_name):
    """调用引擎工具"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    try:
        data = request.get_json(force=True, silent=True) or {}
        result = _call_fn(tool_name, data)
        return jsonify(result.to_dict())
    except Exception as ex:
        return jsonify(ToolResult(False, error=str(ex)).to_dict())


@api_bp.route("/tools", methods=["GET"])
def list_tools():
    """列出所有可用工具"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    server = _get_server()
    result = server.tools.list_tools()
    return jsonify(result.to_dict() if hasattr(result, "to_dict") else result)


@api_bp.route("/observe", methods=["GET"])
def observe():
    """获取完整世界快照"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    server = _get_server()
    snapshot = server.world.observe()
    return jsonify(snapshot)


@api_bp.route("/summary", methods=["GET"])
def summary():
    """获取世界摘要（实体/规则/任务数量）"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    server = _get_server()
    world = server.world
    return jsonify({
        "entities": len(world.entities),
        "rules": len(world.rules),
        "quests": len(world.quests),
        "tick": world.tick,
        "weather": world.weather,
    })


@api_bp.route("/game-state", methods=["GET"])
def game_state():
    """获取游戏状态（前端渲染用）"""
    return jsonify(_build_game_state())


@api_bp.route("/tick", methods=["POST"])
def tick():
    """推进一帧"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    server = _get_server()
    server.runtime.tick(1.0 / 60.0)
    return jsonify({"tick": server.world.tick})


@api_bp.route("/setup", methods=["POST"])
def setup():
    """设置世界初始状态"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    server = _get_server()
    data = request.get_json(force=True, silent=True) or {}
    if "weather" in data:
        server.world.weather = data["weather"]
    if "player_id" in data:
        server.world.player_entity_id = data["player_id"]
    return jsonify({"success": True})


@api_bp.route("/game-state-3d", methods=["GET"])
def game_state_3d():
    """获取 3D 场景状态"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    server = _get_server()
    state = server.tools.scene_3d.get_state()
    return jsonify(state)


@api_bp.route("/export", methods=["POST"])
def export_package():
    """导出游戏包"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    server = _get_server()
    data = request.get_json(force=True, silent=True) or {}
    root = data.get("root", "")
    output = data.get("output", "")
    try:
        from aetherforge.tools import export_project as _export
        result = _export(root, output, include_viewer=False)
        return jsonify(result)
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)})


@api_bp.route("/validate", methods=["GET"])
def validate_package():
    """验证项目完整性"""
    server = _get_server()
    root = getattr(server.world, "project_root", None)
    if not root:
        return jsonify({"ready": False, "issues": ["No project open"], "warnings": []})
    issues, warnings = [], []
    pj = os.path.join(root, "project.json")
    if not os.path.isfile(pj):
        issues.append("Missing project.json")
    sd = os.path.join(root, "scenes")
    if not os.path.isdir(sd):
        issues.append("Missing scenes/ directory")
    else:
        sc = [f for f in os.listdir(sd) if f.endswith(".scene")]
        if not sc:
            issues.append("No .scene files")
    for d in ["assets", "scripts", "tests", "saves"]:
        dd = os.path.join(root, d)
        if os.path.isdir(dd) and not os.listdir(dd):
            warnings.append(d + "/ is empty")
    return jsonify({"ready": len(issues) == 0, "issues": issues, "warnings": warnings})


@api_bp.route("/launcher", methods=["GET"])
def get_launcher():
    """生成启动脚本"""
    server = _get_server()
    mode = request.args.get("mode", "bat")
    name = "AetherForge Game"
    world = server.world
    if getattr(world, "project_root", None):
        pj = os.path.join(world.project_root, "project.json")
        if os.path.isfile(pj):
            try:
                with open(pj) as f:
                    name = json.load(f).get("name", name)
            except Exception:
                pass
    if mode == "bat":
        content = (
            "@echo off\r\nchcp 65001 >nul\r\necho === "
            + name
            + " ===\r\nset JAR=%~dp0_viewer\\AetherForgeStudio-fat.jar\r\n"
            'java -cp "%JAR%" com.aetherforge.ui.GameViewer "%~dp0project.json"\r\npause\r\n'
        )
        return jsonify({"content": content, "filename": "run.bat"})
    content = (
        "#!/bin/bash\necho \"=== "
        + name
        + ' ===\"\nDIR="$(cd "$(dirname "$0")" 2>/dev/null && echo "$PWD")"\n'
        + 'java -cp "$DIR/_viewer/AetherForgeStudio-fat.jar" com.aetherforge.ui.GameViewer "$DIR/project.json"\n'
    )
    return jsonify({"content": content, "filename": "run.sh"})

# ════════════════════════════════════════════
#  模型管理路由
# ════════════════════════════════════════════


@api_bp.route("/models/list", methods=["GET"])
def list_models():
    """列出所有可用模型（图像/音乐/音效）"""
    server = _get_server()
    from aetherforge.tools.model_manager import model_mgr
    models = model_mgr.list_all_models()
    return jsonify({"success": True, "models": models})


@api_bp.route("/models/download", methods=["POST"])
def download_model():
    """下载 AI 模型"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    data = request.get_json(force=True, silent=True) or {}
    model_id = data.get("model_id", "")
    if not model_id:
        return jsonify({"success": False, "error": "model_id required"})
    from aetherforge.tools.model_manager import model_mgr
    result = model_mgr.download_selected_model(model_id)
    return jsonify(result)


@api_bp.route("/models/downloads", methods=["GET"])
def get_downloads():
    """获取当前下载进度"""
    server = _get_server()
    from aetherforge.tools.model_manager import model_mgr
    downloads = model_mgr.get_model_downloads()
    return jsonify({"success": True, "downloads": downloads})


@api_bp.route("/models/select", methods=["POST"])
def select_model():
    """选择激活的模型"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    data = request.get_json(force=True, silent=True) or {}
    model_type = data.get("model_type", "image")
    model_id = data.get("model_id", "")
    if not model_id:
        return jsonify({"success": False, "error": "model_id required"})
    from aetherforge.tools.model_manager import model_mgr
    result = model_mgr.select_generated_model(model_type, model_id)
    return jsonify(result)


@api_bp.route("/models/delete", methods=["DELETE"])
def delete_model():
    """删除已下载的模型"""
    auth_result = _check_auth()
    if auth_result:
        return auth_result
    data = request.get_json(force=True, silent=True) or {}
    model_id = data.get("model_id", "")
    if not model_id:
        return jsonify({"success": False, "error": "model_id required"})
    from aetherforge.tools.model_manager import model_mgr
    result = model_mgr.delete_model(model_id)
    return jsonify(result)
