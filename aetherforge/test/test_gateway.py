"""Tests for Tool Gateway and Permission Manager."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aetherforge.runtime.permissions import PermissionManager, AgentRole, ToolPermission
from aetherforge.agents.gateway import ToolGateway
from aetherforge.agents.errors import PermissionDenied
from aetherforge.validation.evidence import EvidenceStore

# Mock engine for testing
class MockEngine:
    def __init__(self):
        self.entities = {}

    def list_tools(self):
        return {"success": True, "data": {"tools": [{"name": "observe"}, {"name": "create_entity"}]}}

    def observe(self):
        return {"success": True, "data": {"entities": list(self.entities.values())}}

    def create_entity(self, name="", entity_type="generic"):
        eid = f"ent_{len(self.entities) + 1}"
        self.entities[eid] = {"id": eid, "name": name, "type": entity_type}
        return {"success": True, "data": {"entity_id": eid}}

    def get_entity(self, entity_id):
        ent = self.entities.get(entity_id)
        if ent:
            return {"success": True, "data": ent}
        return {"success": False, "error": "not found"}

    def modify_entity(self, entity_id, changes):
        if entity_id in self.entities:
            self.entities[entity_id].update(changes)
            return {"success": True, "data": self.entities[entity_id]}
        return {"success": False, "error": "not found"}

# --- Permission Manager Tests ---

def test_explorer_read_only():
    pm = PermissionManager()
    assert pm.can_call(AgentRole.EXPLORER, "observe") == True
    assert pm.can_call(AgentRole.EXPLORER, "get_entity") == True
    assert pm.can_call(AgentRole.EXPLORER, "create_entity") == False
    assert pm.can_call(AgentRole.EXPLORER, "commit_change") == False
    print("  [PASS] explorer_read_only")

def test_builder_write():
    pm = PermissionManager()
    assert pm.can_call(AgentRole.BUILDER, "observe") == True
    assert pm.can_call(AgentRole.BUILDER, "create_entity") == True
    assert pm.can_call(AgentRole.BUILDER, "modify_entity") == True
    assert pm.can_call(AgentRole.BUILDER, "commit_change") == False
    print("  [PASS] builder_write")

def test_admin_full_access():
    pm = PermissionManager()
    assert pm.can_call(AgentRole.ORCHESTRATOR, "commit_change") == True
    assert pm.can_call(AgentRole.ORCHESTRATOR, "rollback_change") == True
    assert pm.can_call(AgentRole.ORCHESTRATOR, "observe") == True
    assert pm.can_call(AgentRole.ORCHESTRATOR, "create_entity") == True
    print("  [PASS] admin_full_access")

def test_verifier_read():
    pm = PermissionManager()
    assert pm.can_call(AgentRole.VERIFIER, "observe") == True
    assert pm.can_call(AgentRole.VERIFIER, "get_entity") == True
    assert pm.can_call(AgentRole.VERIFIER, "create_entity") == False
    assert pm.can_call(AgentRole.VERIFIER, "commit_change") == False
    print("  [PASS] verifier_read")

# --- Tool Gateway Tests ---

def test_gateway_explorer():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.EXPLORER)
    result = gw.observe()
    assert result["success"] == True
    try:
        gw.create_entity(name="test")
        assert False, "Should have raised PermissionDenied"
    except PermissionDenied:
        pass
    print("  [PASS] gateway_explorer")

def test_gateway_builder():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.BUILDER)
    result = gw.create_entity(name="Guard")
    assert result["success"] == True
    eid = result["data"]["entity_id"]
    result2 = gw.get_entity(eid)
    assert result2["success"] == True
    print("  [PASS] gateway_builder")

def test_gateway_captures_evidence():
    eng = MockEngine()
    es = EvidenceStore()
    gw = ToolGateway(eng, evidence_store=es)
    gw.set_role(AgentRole.BUILDER)

    # Create an entity - should capture evidence
    result = gw.create_entity(name="Village")
    assert result["success"] == True

    # Check evidence was captured
    all_ev = es.find_evidence(source_tool="create_entity")
    assert len(all_ev) >= 1
    assert all_ev[0].source_tool == "create_entity"
    print(f"  [PASS] gateway_captures_evidence: {len(all_ev)} evidence items")

def test_gateway_unknown_tool():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.ORCHESTRATOR)
    result = gw.call_tool("nonexistent_tool")
    assert result["success"] == False
    assert "Unknown tool" in result["error"]
    print("  [PASS] gateway_unknown_tool")

if __name__ == "__main__":
    tests = [test_explorer_read_only, test_builder_write, test_admin_full_access,
             test_verifier_read, test_gateway_explorer, test_gateway_builder,
             test_gateway_captures_evidence, test_gateway_unknown_tool]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\nResult: {passed}/{passed+failed} passed, {failed} failed")