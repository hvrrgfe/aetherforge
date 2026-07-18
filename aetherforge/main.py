'''
AetherForge Main Entry - Integrated game server with runtime.
'''
import sys, os, json, threading, time, webbrowser
from flask import Flask, request, jsonify, send_from_directory
from aetherforge.core.world_model import WorldModel
from aetherforge.api.tools import EngineTools, ToolResult
from aetherforge.runtime.game_loop import GameRuntime

HERE = os.path.dirname(os.path.abspath(__file__))

class AetherForgeServer:
    def __init__(self, host="127.0.0.1", port=7890):
        self.host, self.port = host, port
        self.world = WorldModel()
        self.tools = EngineTools(self.world)
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
            return ToolResult(False, error=f"Unknown tool: {tool_name}")

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
            snap = self.world.snapshot()
            entities = []
            for eid, ed in snap.entities.items():
                pos = ed.get("position",{}); viz = ed.get("visual",{})
                entities.append({
                    "id": eid, "name": ed.get("name",""), "type": ed.get("semantic_type",""),
                    "x": pos.get("x",0), "y": pos.get("y",0),
                    "width": ed.get("size",{}).get("width",32),
                    "height": ed.get("size",{}).get("height",32),
                    "color": viz.get("color","#888"), "shape": viz.get("shape","rectangle"),
                    "state": ed.get("state",{}), "is_player": eid == snap.player_entity_id,
                })
            return jsonify({"tick":snap.tick,"weather":snap.weather,
                "game_time":snap.game_time,"entities":entities,
                "player_entity_id":snap.player_entity_id})

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
            return send_from_directory(static_dir, "index.html")

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
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

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
