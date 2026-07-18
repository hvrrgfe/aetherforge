"""AetherForge API Server - Flask-based REST API for AI control."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

    @app.route("/")
    def index():
        return send_from_directory(static_dir, "index.html")

    return app, tools, world
