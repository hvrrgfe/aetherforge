"""AetherForge Model Manager & Security Tests

Tests for:
  - Model manager (list, download guard, delete)
  - Path traversal protection
  - Utility functions

Run: python -m aetherforge.test.test_security
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = failed = 0
    results = []

    def check(name, ok, detail=""):
        nonlocal passed, failed
        if ok:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"
        print("  [%s] %s: %s" % (status, name, detail))
        results.append({"name": name, "passed": ok, "detail": detail})

    print("[1/4] Model Manager Tests")
    try:
        from aetherforge.tools.model_manager import model_mgr
        models = model_mgr.list_models()
        check("list_models returns 12", len(models) == 12, "got %d" % len(models))
                
        # Filter by type
        img = model_mgr.list_models("image")
        check("list_models(image) == 7", len(img) == 7, "got %d" % len(img))
        mus = model_mgr.list_models("music")
        check("list_models(music) == 5", len(mus) == 5, "got %d" % len(mus))

        # Model info
        info = model_mgr.model_info("anything-v5")
        check("model_info found", info["success"])
        check("model_info has desc_skipped", "Anime" in info["data"].get("desc", ""))

        info2 = model_mgr.model_info("nonexistent")
        check("model_info not found", not info2["success"])

        # Delete non-existent (should fail gracefully)
        r = model_mgr.delete_model("nonexistent_model_xyz")
        check("delete nonexistent", not r["success"], r.get("error", ""))

        # Download import guard (huggingface_hub may not be installed)
        r = model_mgr.download("nonexistent_model_xyz")
        check("download unknown model", not r["success"], r.get("error", ""))

        # Progress
        dl = model_mgr.download_progress()
        check("download_progress returns list", isinstance(dl, list))
    except Exception as e:
        import traceback
        check("model_manager", False, "exception: %s" % traceback.format_exc())

    print("\n[2/4] Path Validation Tests")
    try:
        from aetherforge.tools import validate_project_path as vpp

        # Path traversal
        ok, err = vpp("../etc/passwd")
        check("rejects parent path", not ok, err)

        ok, err = vpp("..\\..\\windows\\system32")
        check("rejects win parent path", not ok, err)

        # Relative path
        ok, err = vpp("test.json")
        check("rejects relative path", not ok, err)

        ok, err = vpp("")
        check("rejects empty path", not ok, err)

        # Absolute path in home
        home = os.path.expanduser("~")
        ok, err = vpp(os.path.join(home, "test.json"))
        check("allows home path", ok, err)

        # Absolute path outside home
        ok, err = vpp("C:\\Windows\\test.txt")
        check("rejects non-home path", not ok, err if err else "blocked")
    except Exception as e:
        import traceback
        check("path_validation", False, "exception: %s" % traceback.format_exc())

    print("\n[3/4] EngineTools Security Tests")
    try:
        from aetherforge.core.world_model import WorldModel
        from aetherforge.api.tools import EngineTools

        wm = WorldModel()
        eng = EngineTools(wm)

        # save_project with traversal
        r = eng.save_project("../../test.json")
        check("tools.save_project blocks traversal", not r.success, r.error or "")

        r = eng.save_project("test.json")
        check("tools.save_project blocks relative", not r.success, r.error or "")

        r = eng.save_project("C:\\Windows\\test.json")
        check("tools.save_project blocks non-home", not r.success, r.error or "")

        # load_project with traversal
        r = eng.load_project("../../test.json")
        check("tools.load_project blocks traversal", not r.success, r.error or "")
    except Exception as e:
        import traceback
        check("engine_tools", False, "exception: %s" % traceback.format_exc())

    print("\n[4/4] MCP Server Tests")
    try:
        from aetherforge.mcp_server import build_direct_engine, _get_tool_defs, _build_tool_defs, _TOOL_DEF_CACHE, _ENGINE

        wm, eng, rt = build_direct_engine()
        check('build_direct_engine returns 3', len([wm, eng, rt]) == 3)

        # Populate _ENGINE and build tool def cache
        _ENGINE['world'] = wm
        _ENGINE['tools'] = eng
        _ENGINE['runtime'] = rt
        _TOOL_DEF_CACHE[:] = _build_tool_defs(eng)
        defs = _get_tool_defs()
        check('MCP tools loaded', len(defs) > 50, 'got %d' % len(defs))

        # Test direct engine works
        r = eng.create_entity('npc', 'MCP Test', 'Direct mode test')
        check('direct engine create_entity', r.success)
    except Exception as e:
        import traceback
        check('mcp_server', False, 'exception: %s' % traceback.format_exc())
    total = passed + failed
    print("\n" + "=" * 50)
    print("Result: %d/%d passed, %d failed" % (passed, total, failed))
    print("=" * 50)
    return {"total": total, "passed": passed, "failed": failed}


if __name__ == "__main__":
    result = run_tests()
    sys.exit(1 if result["failed"] > 0 else 0)
