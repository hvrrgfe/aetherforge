"""Tests for Agent Roles and Orchestrator."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aetherforge.agents.roles import Explorer, Planner, Builder, Verifier, Critic
from aetherforge.agents.orchestrator import AgentOrchestrator
from aetherforge.agents.gateway import ToolGateway
from aetherforge.agents.state import AgentStateManager
from aetherforge.agents.policies import AgentPolicy, TokenBudget
from aetherforge.agents.protocol import TaskState, TaskPhase, Evidence
from aetherforge.validation.evidence import EvidenceStore
from aetherforge.validation.commit_gate import CommitGate, GatePolicy
from aetherforge.runtime.permissions import AgentRole, PermissionManager

class MockEngine:
    def __init__(self):
        self.entities = {}

    def list_tools(self):
        return {"success": True, "data": {"tools": []}}

    def observe(self):
        return {"success": True, "data": {"entities": list(self.entities.values()),
                "entity_count": len(self.entities)}}

    def create_entity(self, name="", semantic_type="generic", description="",
                      capabilities=None, **kw):
        import uuid
        eid = f"ent_{uuid.uuid4().hex[:8]}"
        self.entities[eid] = {"id": eid, "name": name, "type": semantic_type,
                              "description": description, "capabilities": capabilities or []}
        return {"success": True, "data": {"entity_id": eid, "entity": self.entities[eid]}}

    def get_entity(self, entity_id):
        ent = self.entities.get(entity_id)
        if ent:
            return {"success": True, "data": ent}
        return {"success": False, "error": "not found"}

    def find_entities(self, query=""):
        return {"success": True, "data": {"count": len(self.entities),
                "entities": list(self.entities.values())}}

    def modify_entity(self, entity_id, changes):
        if entity_id in self.entities:
            self.entities[entity_id].update(changes)
            return {"success": True, "data": self.entities[entity_id]}
        return {"success": False, "error": "not found"}

class MockWorld:
    def __init__(self):
        self.entities = {}
        self.rules = {}
        self.quests = {}
        self.behaviors = {}
        self.player_entity_id = None
        self._history = []

    def _checkpoint(self):
        import copy
        self._history.append(copy.deepcopy({"entities": self.entities}))
    def get_entity(self, eid):
        return self.entities.get(eid)

# --- Explorer Tests ---

def test_explorer_read_only():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.EXPLORER)
    exp = Explorer(gw)
    result = exp.explore()
    assert "facts" in result
    assert result["fact_count"] >= 0
    print(f"  [PASS] explorer_read_only: {result['fact_count']} facts, {result['constraint_count']} constraints")

def test_explorer_add_facts():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.EXPLORER)
    exp = Explorer(gw)
    exp.add_fact("Entity exists", "observe")
    exp.add_unknown("Is the door locked?")
    result = exp._build_report()
    assert result["fact_count"] == 1
    assert result["unknown_count"] == 1
    print("  [PASS] explorer_add_facts")

# --- Planner Tests ---

def test_planner_create_plan():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.PLANNER)
    plan = Planner(gw)
    explorer_out = {"facts": [], "unknowns": [], "constraints": [], "fact_count": 0}
    result = plan.create_plan(explorer_out, "Create a village")
    assert "plan_id" in result
    assert "steps" in result
    print("  [PASS] planner_create_plan")

def test_planner_add_steps():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.PLANNER)
    plan = Planner(gw)
    p = plan.create_plan({"facts": [], "unknowns": [], "constraints": []}, "Test")
    plan.add_step(p, "Create guard", "create_entity", {"name": "Guard"})
    plan.add_step(p, "Create house", "create_entity", {"name": "House"})
    plan.add_criterion(p, "Guard exists", "entity_exists", {"entity_id": "guard_1"})
    assert len(p["steps"]) == 2
    assert len(p["acceptance_criteria"]) == 1
    print("  [PASS] planner_add_steps: 2 steps, 1 criterion")

# --- Builder Tests ---

def test_builder_execute():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.BUILDER)
    builder = Builder(gw)
    plan = {"plan_id": "plan_1", "steps": [
        {"step_id": "step_1", "tool": "create_entity", "params": {"name": "Guard", "semantic_type": "npc"}},
        {"step_id": "step_2", "tool": "create_entity", "params": {"name": "House", "semantic_type": "building"}},
    ]}
    result = builder.execute_plan(plan)
    assert result["passed"] == 2
    assert result["failed"] == 0
    print(f"  [PASS] builder_execute: {result['passed']}/{result['total_steps']}")

# --- Verifier Tests ---

def test_verifier_check_evidence():
    eng = MockEngine()
    es = EvidenceStore()
    gw = ToolGateway(eng, evidence_store=es)
    gw.set_role(AgentRole.VERIFIER)
    ver = Verifier(gw, es)
    result = ver.verify_evidence_chain("task_nonexistent")
    assert "passed" in result
    print(f"  [PASS] verifier_check_evidence")

# --- Critic Tests ---

def test_critic_review():
    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.CRITIC)
    crit = Critic(gw)
    world = MockWorld()
    world.entities["e1"] = type("E", (), {"name": "Guard"})()
    result = crit.review("task_1", world)
    assert "issues" in result
    print(f"  [PASS] critic_review: {result['total_issues']} issues")

# --- Orchestrator Tests ---

def test_orchestrator_start_task():
    world = MockWorld()
    eng = MockEngine()
    es = EvidenceStore()
    gw = ToolGateway(eng, evidence_store=es)
    sm = AgentStateManager()
    cg = CommitGate(GatePolicy.NORMAL)
    orch = AgentOrchestrator(world, gw, es, cg, sm)
    result = orch.start_task("Create a village")
    assert "task_id" in result
    assert result["status"] == "planning"
    task = sm.get_task(result["task_id"])
    assert task is not None
    print(f"  [PASS] orchestrator_start_task: {result['task_id']}")

def test_orchestrator_get_report():
    world = MockWorld()
    eng = MockEngine()
    es = EvidenceStore()
    gw = ToolGateway(eng, evidence_store=es)
    sm = AgentStateManager()
    cg = CommitGate(GatePolicy.NORMAL)
    orch = AgentOrchestrator(world, gw, es, cg, sm)
    result = orch.start_task("Test task")
    report = orch.get_report(result["task_id"])
    assert report["goal"] == "Test task"
    print("  [PASS] orchestrator_get_report")

def test_orchestrator_rollback():
    world = MockWorld()
    eng = MockEngine()
    es = EvidenceStore()
    gw = ToolGateway(eng, evidence_store=es)
    sm = AgentStateManager()
    cg = CommitGate(GatePolicy.NORMAL)
    orch = AgentOrchestrator(world, gw, es, cg, sm)
    result = orch.start_task("Test rollback")
    rb = orch.rollback_task(result["task_id"])
    assert rb["success"]
    print("  [PASS] orchestrator_rollback")

if __name__ == "__main__":
    tests = [test_explorer_read_only, test_explorer_add_facts, test_planner_create_plan,
             test_planner_add_steps, test_builder_execute, test_verifier_check_evidence,
             test_critic_review, test_orchestrator_start_task, test_orchestrator_get_report,
             test_orchestrator_rollback]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            import traceback
            print(f"  [FAIL] {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\nResult: {passed}/{passed+failed} passed, {failed} failed")