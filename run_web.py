"""AetherForge Web Server - Start Flask with HTTP API + Static Files."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from aetherforge.api.server import create_server
from aetherforge.core.world_model import WorldModel

def main():
    world = WorldModel()
    app, tools, world_model = create_server(world)
    print(f"[AetherForge] Web server starting on http://127.0.0.1:7890")
    print(f"[AetherForge] Open in browser or AetherForgeStudio WebView2 client")
    app.run(host="127.0.0.1", port=7890, debug=False)

if __name__ == "__main__":
    main()