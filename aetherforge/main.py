'''
AetherForge Main Entry - Integrated game server with runtime.
'''
import sys, os, json, threading, time
from flask import Flask, request, jsonify, send_from_directory
from aetherforge.core.world_model import WorldModel
from aetherforge.api.tools import ToolResult
from aetherforge.api.engine_v2 import EngineToolsV2
from aetherforge.runtime.game_loop import GameRuntime

if getattr(sys, 'frozen', False):
    HERE = sys._MEIPASS
else:
    HERE = os.path.dirname(os.path.abspath(__file__))

class AetherForgeServer:
    def __init__(self, host="127.0.0.1", port=7890):
        self.host, self.port = host, port
        self.world = WorldModel()
        self.tools = EngineToolsV2(self.world)
        self.runtime = GameRuntime(self.world)
        self._make_app()

    def _make_app(self):
        static_dir = os.path.join(HERE, "static")
        app = Flask(__name__, static_folder=static_dir, static_url_path="")
        app.config["SECRET_KEY"] = os.environ.get("AETHERFORGE_SECRET_KEY", "dev-secret-change-in-production")
        tools, runtime = self.tools, self.runtime

        def call_fn(tool_name, data):
            if not isinstance(tool_name, str) or not tool_name.isidentifier():
                return ToolResult(False, error="Invalid tool name")
            fn = getattr(tools, tool_name, None)
            if fn:
                return fn(**data)
            if tool_name == "tick":
                runtime.tick(data.get("dt", 1.0/60.0))
                return ToolResult(True, {"tick": self.world.tick})
            if tool_name == "set_player_input":
                runtime.set_player_input(**{k: data.get(k, False) for k in ["up","down","left","right"]})
                return ToolResult(True, {})
            if tool_name == "player_interact":
                r = runtime.player_interact()
                return ToolResult(r.get("success", False), data=r)
            if tool_name == "step":
                runtime.tick(1.0/60.0)
                return ToolResult(True, {"tick": self.world.tick})
            if tool_name == "pause":
                runtime.pause(); return ToolResult(True, {})
            if tool_name == "resume":
                runtime.resume(); return ToolResult(True, {})
            if tool_name == "set_time_scale":
                runtime.set_time_scale(data.get("scale",1.0))
                return ToolResult(True, {})
            if tool_name == "modify_entity_quick":
                ok = self.world.quick_modify_entity(data.get("entity_id",""), data.get("changes",{}))
                return ToolResult(ok, {})
            if tool_name == "remove_entity_quick":
                ok = self.world.quick_remove_entity(data.get("entity_id",""))
                return ToolResult(ok, {})
            return ToolResult(False, error=f"Unknown tool: {tool_name}")

        def _build_game_state():
            """Build game-state dict directly from world entities, no snapshot overhead."""
            entities = []
            for eid, e in self.world.entities.items():
                pos = e.position if hasattr(e, 'position') else {}
                viz = e.visual if hasattr(e, 'visual') else {}
                sz = e.size if hasattr(e, 'size') else {}
                entities.append({
                    "id": eid, "name": e.name if hasattr(e, 'name') else "",
                    "type": e.semantic_type if hasattr(e, 'semantic_type') else "",
                    "x": pos.get("x", 0), "y": pos.get("y", 0),
                    "width": sz.get("width", 32), "height": sz.get("height", 32),
                    "color": viz.get("color", "#888"), "shape": viz.get("shape", "rectangle"),
                    "state": e.state if hasattr(e, 'state') else {},
                    "is_player": eid == self.world.player_entity_id,
                })
            return {
                "tick": self.world.tick, "weather": self.world.weather,
                "game_time": self.world.game_time, "entities": entities,
                "player_entity_id": self.world.player_entity_id,
            }

        @app.after_request
        def add_security_headers(response):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            return response

        @app.route("/api/tools/<tool_name>", methods=["POST"])
        def call_tool(tool_name):
            try:
                result = call_fn(tool_name, request.get_json(silent=True) or {})
                return jsonify(result.to_dict())
            except Exception as ex:
                return jsonify(ToolResult(False, error=str(ex)).to_dict()), 500

        @app.route("/api/tools", methods=["GET"], strict_slashes=False)
        def list_tools():
            return jsonify(tools.list_tools().to_dict())

        @app.route("/api/observe", methods=["GET"])
        def observe():
            return jsonify(tools.observe().to_dict())

        @app.route("/api/summary", methods=["GET"])
        def summary():
            return jsonify(self.world.summary)

        @app.route("/api/game-state", methods=["GET"])
        def game_state():
            return jsonify(_build_game_state())

        @app.route("/api/tick", methods=["POST"])
        def tick_combined():
            """Generic tick: accepts player input + dt, returns game state in one request."""
            try:
                data = request.get_json(silent=True) or {}
                dt = data.get("dt", 1.0 / 60.0)
                # Apply player input (if any)
                inp = {k: data.get(k, False) for k in ["up", "down", "left", "right"]}
                runtime.set_player_input(**inp)
                # Tick the game world
                runtime.tick(dt)
                return jsonify(_build_game_state())
            except Exception as ex:
                return jsonify({"tick": self.world.tick, "error": str(ex), "entities": []}), 500

        @app.route("/api/setup", methods=["POST"])
        def setup_world():
            """Clear world to empty slate. Optionally create a default player entity."""
            try:
                world = self.world
                data = request.get_json(silent=True) or {}
                for eid in list(world.entities):
                    world.quick_remove_entity(eid)
                for rid in list(world.rules):
                    world.remove_rule(rid)
                # Optionally create a player entity
                if data.get("create_player"):
                    from aetherforge.core import SemanticEntity
                    pos = data.get("position", {"x": 400, "y": 300})
                    player = SemanticEntity(
                        entity_id=data.get("player_id", "player"),
                        semantic_type="player", name=data.get("name", "Player"),
                        description="The player character",
                        position=pos,
                        visual=data.get("visual", {"color": "#00ccff", "shape": "rectangle"}),
                        size=data.get("size", {"width": 32, "height": 32}),
                        state=data.get("state", {}))
                    world.create_entity(player)
                    world.player_entity_id = player.entity_id
                    return jsonify({"success": True, "player_id": player.entity_id})
                return jsonify({"success": True, "player_id": None})
            except Exception as ex:
                return jsonify({"success": False, "error": str(ex)}), 500

        @app.route("/api/game-state-3d", methods=["GET"])
        def game_state_3d():
            from aetherforge.renderer import SceneGraph3D
            sg = SceneGraph3D(self.world)
            for eid, ent in self.world.entities.items():
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
            state["tick"] = self.world.tick
            state["game_time"] = self.world.game_time
            return jsonify(state)

        @app.route("/")
        def index():
            return app.send_static_file("index.html")

        @app.route("/viewer-3d")
        def viewer_3d():
            return send_from_directory(static_dir, "viewer_3d.html")

        self.app = app
    def start(self):
        print(f"  AetherForge Engine")
        print(f"  API:     http://{self.host}:{self.port}/api/")
        print(f"  Tools:   http://{self.host}:{self.port}/api/tools/")
        print(f"  Observe: http://{self.host}:{self.port}/api/observe")
        print(f"  Game:    http://{self.host}:{self.port}/")
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False, threaded=True)

def main():
    import argparse
    ap = argparse.ArgumentParser(description="AetherForge")
    ap.add_argument("--demo", action="store_true", help="Load rainy station demo")
    ap.add_argument("--demo-3d", action="store_true", help="Load 3D rainy station demo")
    ap.add_argument("--host", default="127.0.0.1", help="Server host")
    ap.add_argument("--port", type=int, default=7890, help="Server port")
    ap.add_argument("--project", type=str, help="Load project file")
    args = ap.parse_args()

    srv = AetherForgeServer(host=args.host, port=args.port)

    if args.demo:
        from aetherforge.demo.station import demo_setup
        demo_setup(srv.tools)
    if args.demo_3d:
        from aetherforge.api.engine_v2 import EngineToolsV2
        srv.tools = EngineToolsV2(srv.world)
        from aetherforge.demo.station_3d import demo_3d_setup
        demo_3d_setup(srv.tools)
    if args.project:
        srv.tools.load_project(args.project)
    srv.start()

if __name__ == "__main__":
    main()
