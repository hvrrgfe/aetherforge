"""AetherForge API Server - Flask-based REST API for AI control."""
import sys, os, json
from flask import Flask, request, jsonify, send_from_directory
from aetherforge.core.world_model import WorldModel
from aetherforge.api.tools import EngineTools, ToolResult


def create_server(world=None):
    if world is None:
        world = WorldModel()
    tools = EngineTools(world)
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.config["SECRET_KEY"] = os.environ.get(
        "AETHERFORGE_SECRET_KEY", "dev-secret-change-in-production"
    )

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.route("/api/tools/<tool_name>", methods=["POST"])
    def call_tool(tool_name):
        fn = getattr(tools, tool_name, None)
        if not fn:
            return jsonify(ToolResult(False, error=f"Unknown tool: {tool_name}").to_dict()), 404
        try:
            data = request.get_json(silent=True) or {}
            # Path traversal guard (defense in depth)
            if tool_name in ('save_project', 'load_project'):
                from aetherforge.tools import validate_project_path as _vpp
                ok, err = _vpp(data.get('path', ''))
                if not ok:
                    return jsonify(ToolResult(False, error=err).to_dict()), 403
            result = fn(**data)
            return jsonify(result.to_dict())
        except Exception as ex:
            return jsonify(ToolResult(False, error=str(ex)).to_dict()), 500

    @app.route("/api/tools", methods=["GET"])
    @app.route("/api/tools/<tool_name>", methods=["GET"])
    def list_or_get_tool(tool_name=None):
        if tool_name:
            return jsonify({"name": tool_name, "doc": getattr(tools, tool_name, None).__doc__ or ""})
        return jsonify(tools.list_tools().to_dict())

    @app.route("/api/observe", methods=["GET"])
    def observe():
        return jsonify(tools.observe().to_dict())

    @app.route("/api/summary", methods=["GET"])
    def summary():
        return jsonify(world.summary)

    @app.route("/api/game-state", methods=["GET"])
    def game_state():
        snap = world.snapshot()
        entities = []
        for eid, ed in snap.entities.items():
            pos = ed.get("position", {})
            viz = ed.get("visual", {})
            entities.append({
                "id": eid, "name": ed.get("name", ""), "type": ed.get("semantic_type", ""),
                "x": pos.get("x", 0), "y": pos.get("y", 0),
                "width": ed.get("size", {}).get("width", 32),
                "height": ed.get("size", {}).get("height", 32),
                "color": viz.get("color", "#888"), "shape": viz.get("shape", "rectangle"),
                "state": ed.get("state", {}),
                "is_player": eid == snap.player_entity_id,
            })
        return jsonify({
            "tick": snap.tick, "weather": snap.weather,
            "game_time": snap.game_time, "entities": entities,
            "player_entity_id": snap.player_entity_id,
        })

    @app.route("/api/game-state-3d", methods=["GET"])
    def game_state_3d():
        """Return 3D scene state for Three.js viewer."""
        from aetherforge.renderer import SceneGraph3D
        sg = SceneGraph3D(world)
        for eid, ent in world.entities.items():
            pos = ent.position if hasattr(ent, "position") else {"x": 0, "y": 0}
            vis = ent.visual if hasattr(ent, "visual") else {"color": "#888", "shape": "box"}
            tf = {
                "position": {"x": pos.get("x", 0), "y": pos.get("y", 0), "z": 0},
                "rotation": {"x": 0, "y": 0, "z": 0},
                "scale": {"x": 1, "y": 1, "z": 1},
            }
            mesh = {
                "geometry": "box", "color": vis.get("color", "#888"),
                "texture": "", "emissive": "#000000",
                "metalness": 0, "roughness": 0.8,
            }
            sg.set_transform(eid, tf)
            sg.set_mesh(eid, mesh)
        state = sg.get_3d_state()
        state["tick"] = world.tick
        state["game_time"] = world.game_time
        return jsonify(state)

    
    # ==================== Model Management API ====================

    @app.route("/api/models/search", methods=["GET"])
    def search_models():
        """Search models from Hugging Face by type and query."""
        from aetherforge.tools.model_manager import model_mgr
        query = request.args.get("query", "")
        model_type = request.args.get("model_type", "")
        limit = int(request.args.get("limit", "30"))
        result = model_mgr.search_online_models(query, model_type, limit)
        return jsonify(result)

    @app.route("/api/models/list", methods=["GET"])
    def list_models():
        """List all known and locally downloaded models."""
        from aetherforge.tools.model_manager import model_mgr
        model_type = request.args.get("model_type", "")
        results = model_mgr.list_all_models(model_type)
        return jsonify({"success": True, "count": len(results), "models": results})

    @app.route("/api/models/download", methods=["POST"])
    def download_model():
        """Start downloading a model in background."""
        from aetherforge.tools.model_manager import model_mgr
        data = request.get_json(silent=True) or {}
        model_id = data.get("model_id", "")
        if not model_id:
            return jsonify({"success": False, "error": "model_id required"}), 400
        result = model_mgr.download_selected_model(model_id)
        return jsonify(result)

    @app.route("/api/models/downloads", methods=["GET"])
    def model_downloads():
        """Get current download progress."""
        from aetherforge.tools.model_manager import model_mgr
        return jsonify({"downloads": model_mgr.get_model_downloads()})

    @app.route("/api/models/select", methods=["POST"])
    def select_model():
        """Select a downloaded model for generation."""
        from aetherforge.tools.model_manager import model_mgr
        data = request.get_json(silent=True) or {}
        model_type = data.get("model_type", "")
        model_id = data.get("model_id", "")
        if not model_type or not model_id:
            return jsonify({"success": False, "error": "model_type and model_id required"}), 400
        result = model_mgr.select_generated_model(model_type, model_id)
        return jsonify(result)

    @app.route("/api/models/selected", methods=["GET"])
    def selected_models():
        """Get currently selected models."""
        from aetherforge.tools.model_manager import model_mgr
        return jsonify(model_mgr.get_selected_models())

    @app.route("/api/models/info/<path:model_id>", methods=["GET"])
    def model_info(model_id):
        """Get detailed info about a specific model."""
        from aetherforge.tools.model_manager import model_mgr
        result = model_mgr.model_info(model_id)
        return jsonify(result)

    @app.route("/api/models/delete", methods=["POST"])
    def delete_model():
        """Delete a locally downloaded model."""
        from aetherforge.tools.model_manager import model_mgr
        data = request.get_json(silent=True) or {}
        model_id = data.get("model_id", "")
        if not model_id:
            return jsonify({"success": False, "error": "model_id required"}), 400
        result = model_mgr.delete_model(model_id)
        return jsonify(result)
@app.route("/")
    def index():
        return send_from_directory(static_dir, "index.html")

    return app, tools, world
