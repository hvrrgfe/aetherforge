"""Model Router Setup - configure endpoint and API key."""
import os, sys, argparse

_not_set = "(not set)"

def setup_router(endpoint="", api_key="", model_name="", max_tokens=0, save=True):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from aetherforge.config import get_config, save_config
    cfg = get_config()
    changed = []
    if endpoint:
        cfg.agent.endpoint = endpoint.rstrip("/")
        changed.append("endpoint")
    if api_key:
        cfg.agent.api_key = api_key
        changed.append("api_key")
    if model_name:
        cfg.agent.model_name = model_name
        changed.append("model=" + model_name)
    if max_tokens > 0:
        cfg.agent.max_tokens_per_task = max_tokens
        changed.append("max_tokens=" + str(max_tokens))
    if save and changed:
        path = save_config(cfg)
        return {"success": True, "changes": changed, "config_file": path}
    return {"success": True, "changes": changed}

def show_config():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from aetherforge.config import get_config
    cfg = get_config().agent
    key_status = "***" if cfg.api_key else _not_set
    ep = cfg.endpoint or _not_set
    print("=== Model Router Configuration ===")
    print(f"  Enabled:      {cfg.enabled}")
    print(f"  Endpoint:     {ep}")
    print(f"  API Key:      {key_status}")
    print(f"  Model:        {cfg.model_name}")
    print(f"  Max Tokens:   {cfg.max_tokens_per_task}")
    env_key = os.environ.get("AETHERFORGE_API_KEY", "")
    env_ep = os.environ.get("AETHERFORGE_ENDPOINT", "")
    env_model = os.environ.get("AETHERFORGE_MODEL", "")
    if env_key or env_ep or env_model:
        print("  Env Overrides: set AETHERFORGE_API_KEY / AETHERFORGE_ENDPOINT / AETHERFORGE_MODEL")

def main():
    parser = argparse.ArgumentParser(description="Configure AetherForge Model Router")
    parser.add_argument("--endpoint", help="API endpoint URL")
    parser.add_argument("--api-key", help="API key")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--max-tokens", type=int, default=0)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    if args.show:
        show_config()
    elif any([args.endpoint, args.api_key, args.model, args.max_tokens]):
        result = setup_router(args.endpoint or "", args.api_key or "", args.model or "", args.max_tokens)
        print("Configured:", ", ".join(result["changes"]))
        print("Saved to:", result["config_file"])
    else:
        show_config()

if __name__ == "__main__":
    main()
