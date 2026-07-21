"""AetherForge Main Entry - Integrated game server with runtime.

路由已拆分为 aetherforge/api/routes.py Blueprint。
"""
import sys
import os
import secrets
from flask import Flask, send_from_directory

from aetherforge.core.world_model import WorldModel
from aetherforge.api.engine_v2 import EngineToolsV2
from aetherforge.api.routes import api_bp
from aetherforge.runtime.game_loop import GameRuntime


if getattr(sys, "frozen", False):
    HERE = sys._MEIPASS
else:
    HERE = os.path.dirname(os.path.abspath(__file__))


class AetherForgeServer:
    """AetherForge 游戏服务器 — 整合世界模型、工具引擎和运行时。"""

    def __init__(self, host="127.0.0.1", port=7890):
        self.host = host
        self.port = port
        self.world = WorldModel()
        self.tools = EngineToolsV2(self.world)
        self.runtime = GameRuntime(self.world)
        self._api_token = None
        self._make_app()

    def _make_app(self):
        static_dir = os.path.join(HERE, "static")
        app = Flask(__name__, static_folder=static_dir, static_url_path="")

        app.config["SECRET_KEY"] = os.environ.get(
            "AETHERFORGE_SECRET_KEY", secrets.token_hex(32)
        )

        # API Token 认证（绑定 0.0.0.0 时自动启用）
        self._api_token = os.environ.get(
            "AETHERFORGE_API_TOKEN",
            secrets.token_hex(16) if self.host == "0.0.0.0" else None,
        )
        if self._api_token:
            print(f"  [SECURITY] API token auth enabled: Bearer {self._api_token}", flush=True)

        # 注册 Blueprint，将 server 实例注入 config
        app.config["AETHERFORGE_SERVER"] = self
        app.register_blueprint(api_bp)

        # ─── 静态文件路由 ───
        @app.route("/")
        def index():
            return app.send_static_file("index.html")

        @app.route("/viewer-3d")
        def viewer_3d():
            return send_from_directory(static_dir, "viewer_3d.html")

        # ─── 安全绑定检查 ───
        @app.before_request
        def security_check():
            if self.host in ("0.0.0.0", "::") and not getattr(self, "_allow_external", False):
                return "Server is not configured for external access", 403

        self.app = app

    def start(self):
        print(f"  AetherForge 引擎")
        print(f"  API 接口: http://{self.host}:{self.port}/api/")
        print(f"  工具列表: http://{self.host}:{self.port}/api/tools/")
        print(f"  世界观察: http://{self.host}:{self.port}/api/observe")
        print(f"  游戏界面: http://{self.host}:{self.port}/")
        self.app.run(
            host=self.host,
            port=self.port,
            debug=False,
            use_reloader=False,
            threaded=True,
        )


def main():
    import argparse

    ap = argparse.ArgumentParser(description="AetherForge")
    # (demo flags removed)
    ap.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (use --allow-external for 0.0.0.0)",
    )
    ap.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow binding to 0.0.0.0 (WARNING: no auth)",
    )
    ap.add_argument("--port", type=int, default=7890, help="Server port")
    ap.add_argument("--project", type=str, help="Load project file")
    args = ap.parse_args()

    if args.host in ("0.0.0.0", "::") and not args.allow_external:
        print(
            f"  [SECURITY] ERROR: Refusing to bind to {args.host} "
            "(use --allow-external to override)",
            flush=True,
        )
        print(
            "  [SECURITY] The API has NO authentication. "
            "Anyone on your network can control your game world.",
            flush=True,
        )
        print(
            "  [SECURITY] Run with: python -m aetherforge.main "
            "--allow-external --host 0.0.0.0",
            flush=True,
        )
        sys.exit(1)

    srv = AetherForgeServer(host=args.host, port=args.port)
    srv._allow_external = args.allow_external

    # (demo loading removed - blank engine)

    if args.project:
        srv.tools.load_project(args.project)

    srv.start()


if __name__ == "__main__":
    main()
