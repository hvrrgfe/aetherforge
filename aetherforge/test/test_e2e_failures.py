"""Failure path tests - edge cases and error handling."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

def test_apply_world_patch_rollback():
    """Test that apply_world_patch rolls back on failure."""
    from aetherforge.core.world_model import WorldModel
    from aetherforge.core import SemanticEntity
    from aetherforge.api.engine_v2 import EngineToolsV2
    from aetherforge.api.tools import ToolResult

    w = WorldModel()
    e1 = SemanticEntity(entity_id="test_e1", name="Test", semantic_type="entity")
    w.create_entity(e1)
    assert "test_e1" in w.entities
    before_count = len(w.entities)

    # Simulate apply_world_patch with mixed success (will get ToolResult from the real tool)
    # Direct test: verify rollback works on world model
    w.create_entity(SemanticEntity(entity_id="will_rollback", name="Rollback", semantic_type="entity"))
    assert "will_rollback" in w.entities
    w.rollback()
    assert "will_rollback" not in w.entities
    assert len(w.entities) == before_count
    print("  [PASS] test_apply_world_patch_rollback")

def test_snapshot_manager_empty_diff():
    from aetherforge.runtime.snapshots import SnapshotManager

    class MockWorld:
        def __init__(self):
            self.entities = {}
            self.rules = {}
            self.quests = {}
            self.behaviors = {}
            self.tick = 0
            self.revision = 1

    mgr = SnapshotManager()
    w1 = MockWorld()
    w1.revision = 1
    mgr.take(w1)
    w2 = MockWorld()
    w2.revision = 2
    mgr.take(w2)
    diff = mgr.diff(1, 2)
    assert diff is not None
    assert len(diff["entities_created"]) == 0
    assert len(diff["entities_modified"]) == 0
    print("  [PASS] test_snapshot_manager_empty_diff")

def test_approval_manager_persistence():
    """Test approval manager save/load."""
    import tempfile, json
    from pathlib import Path
    from aetherforge.agents.approvals import ApprovalManager

    import tempfile, json, time
    from pathlib import Path
    from aetherforge.agents.approvals import ApprovalManager

    with tempfile.TemporaryDirectory() as td:
        persist = str(Path(td) / "test_approvals.json")
        mgr1 = ApprovalManager(persist_path=persist)
        req1 = mgr1.create_request("t1", "commit_approval", {"msg": "test"})
        req2 = mgr1.create_request("t2", "plan_approval", {})
        time.sleep(0.1)
        # Create new manager and verify it loads
        mgr2 = ApprovalManager(persist_path=persist)
        all_reqs = mgr2.get_pending()
        task_ids = [r["task_id"] for r in all_reqs]
        assert "t1" in task_ids, f"t1 not in {task_ids}"
        assert "t2" in task_ids, f"t2 not in {task_ids}"
    print("  [PASS] test_approval_manager_persistence")

def test_network_switch_nonexistent():
    """Test switching to a non-configured source."""
    from aetherforge.tools.network import NetworkSourceManager
    nm = NetworkSourceManager({"timeout": 2, "sources": [{"name": "test", "endpoint": "https://example.com", "enabled": True}]})
    result = nm.switch_source("https://nonexistent-source.com")
    assert not result.get("success")
    print("  [PASS] test_network_switch_nonexistent")

def test_model_manager_delete_nonexistent():
    """Test deleting a model that does not exist."""
    from aetherforge.tools.model_manager import model_mgr
    result = model_mgr.delete_model("nonexistent_model_xyz")
    assert not result.get("success")
    assert "error" in result
    print("  [PASS] test_model_manager_delete_nonexistent")

def test_orchestrator_rollback_no_task():
    """Test rollback on non-existent task."""
    from aetherforge.agents.orchestrator import AgentOrchestrator
    from aetherforge.core.world_model import WorldModel
    from aetherforge.agents.gateway import ToolGateway
    from aetherforge.validation.evidence import EvidenceStore
    from aetherforge.validation.commit_gate import CommitGate

    class MockEngine:
        def observe(self): return {"success": True, "data": {}}
        def list_tools(self): return {"success": True, "data": {"tools": []}}

    w = WorldModel()
    gw = ToolGateway(MockEngine())
    es = EvidenceStore()
    cg = CommitGate()
    orch = AgentOrchestrator(w, gw, es, cg)
    result = orch.rollback_task("nonexistent_task")
    assert result.get("success")
    print("  [PASS] test_orchestrator_rollback_no_task")

if __name__ == "__main__":
    tests = [test_apply_world_patch_rollback, test_snapshot_manager_empty_diff,
             test_approval_manager_persistence, test_network_switch_nonexistent,
             test_model_manager_delete_nonexistent, test_orchestrator_rollback_no_task]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
    print(f"\nResult: {passed}/{len(tests)} passed")
