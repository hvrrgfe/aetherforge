"""Tests for agents/approvals.py"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from pathlib import Path
from aetherforge.agents.approvals import ApprovalManager, ApprovalType, ApprovalStatus

def test_create_and_resolve():
    with tempfile.TemporaryDirectory() as td:
        mgr = ApprovalManager(persist_path=str(Path(td) / "ap.json"))
        req = mgr.create_request("t1", "plan_approval", {"plan": "test"}, timeout_seconds=60)
        assert req.status == ApprovalStatus.PENDING
        result = mgr.resolve(req.id, True, "test_user")
        assert result["success"]
        assert result["status"] == "approved"
    print("  [PASS] test_create_and_resolve")

def test_pending_filter():
    with tempfile.TemporaryDirectory() as td:
        mgr = ApprovalManager(persist_path=str(Path(td) / "ap.json"))
        mgr.create_request("t1", "commit_approval", {})
        mgr.create_request("t2", "plan_approval", {})
        pending = mgr.get_pending("t1")
        assert len(pending) == 1
        assert pending[0]["task_id"] == "t1"
    print("  [PASS] test_pending_filter")

def test_reject():
    with tempfile.TemporaryDirectory() as td:
        mgr = ApprovalManager(persist_path=str(Path(td) / "ap.json"))
        req = mgr.create_request("t1", "rollback_approval", {})
        result = mgr.resolve(req.id, False)
        assert result["status"] == "rejected"
    print("  [PASS] test_reject")

def test_unknown_resolve():
    with tempfile.TemporaryDirectory() as td:
        mgr = ApprovalManager(persist_path=str(Path(td) / "ap.json"))
        result = mgr.resolve("nonexistent", True)
        assert not result["success"]
    print("  [PASS] test_unknown_resolve")

if __name__ == "__main__":
    passed = 0
    for t in [test_create_and_resolve, test_pending_filter, test_reject, test_unknown_resolve]:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
    print(f"\nResult: {passed}/4 passed")
