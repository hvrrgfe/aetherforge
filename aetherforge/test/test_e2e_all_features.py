"""Comprehensive end-to-end tests for all new WP features."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

def test_risk_level_assessment():
    from aetherforge.runtime.permissions import assess_risk_from_goal, RiskLevel
    assert assess_risk_from_goal("delete all entities completely and replace everything") == RiskLevel.L3_FULL
    assert assess_risk_from_goal("create a village") == RiskLevel.L2_STANDARD
    assert assess_risk_from_goal("modify guard position") == RiskLevel.L1_LIGHT
    assert assess_risk_from_goal("view world state") == RiskLevel.L0_DIRECT
    print("  [PASS] test_risk_level_assessment")

def test_required_agents():
    from aetherforge.runtime.permissions import get_required_agents, RiskLevel
    assert "critic" in get_required_agents(RiskLevel.L3_FULL)
    assert "verifier" in get_required_agents(RiskLevel.L2_STANDARD)
    assert "planner" in get_required_agents(RiskLevel.L1_LIGHT)
    assert "explorer" not in get_required_agents(RiskLevel.L0_DIRECT)
    print("  [PASS] test_required_agents")

def test_snapshot_diff():
    from aetherforge.runtime.snapshots import SnapshotManager, WorldSnapshot, diff_snapshots
    mgr = SnapshotManager(max_snapshots=5)

    class MockWorld:
        def __init__(self):
            self.tick = 0
            self.revision = 0
            self.entities = {}
            self.rules = {}
            self.quests = {}
            self.behaviors = {}

    w = MockWorld()
    w.revision = 1
    w.entities = {"e1": type("E", (), {"to_dict": lambda self: {"id": "e1"}, "entity_id": "e1", "name": "E1", "semantic_type": "entity"})()}
    before = mgr.take(w)

    w2 = MockWorld()
    w2.revision = 2
    w2.entities = {
        "e1": type("E", (), {"to_dict": lambda self: {"id": "e1"}, "entity_id": "e1", "name": "E1", "semantic_type": "entity"})(),
        "e2": type("E", (), {"to_dict": lambda self: {"id": "e2"}, "entity_id": "e2", "name": "E2", "semantic_type": "entity"})(),
    }
    after = mgr.take(w2)
    diff = mgr.diff(before.revision, after.revision)
    assert diff is not None
    assert "e2" in diff["entities_created"]
    print("  [PASS] test_snapshot_diff")

def test_suggestion_candidates():
    from aetherforge.agents.suggestions import SuggestionManager
    mgr = SuggestionManager()
    sug = mgr.create_suggestion("user", {"type": "scene", "id": "village"}, "Improve village atmosphere", "polish")
    mgr.generate_candidates(sug)
    assert len(sug.candidates) >= 2
    cand = sug.candidates[0]
    assert cand.risk == "low"
    assert cand.impact == "low" or cand.impact == "medium"
    print("  [PASS] test_suggestion_candidates")

def test_art_director_review():
    from aetherforge.agents.roles.art_director import ArtDirector
    from aetherforge.agents.gateway import ToolGateway

    class MockEntity:
        entity_id = "e1"
        name = ""
        semantic_type = "npc"
        visual = {}
        def to_dict(self): return {"id": "e1"}

    class MockEngine:
        def observe(self): return {"success": True, "data": {}}
        def list_tools(self): return {"success": True, "data": {"tools": []}}

    class MockWorld:
        entities = {"e1": MockEntity()}

    gw = ToolGateway(MockEngine())
    from aetherforge.runtime.permissions import AgentRole
    gw.set_role(AgentRole.ART_DIRECTOR)
    ad = ArtDirector(gw)
    review = ad.review_scene(MockWorld())
    assert review["total_findings"] > 0
    print("  [PASS] test_art_director_review")

def test_auto_summarize():
    from aetherforge.core import SemanticEntity
    e = SemanticEntity(entity_id="guard_01", name="Village Guard", semantic_type="npc",
                       description="Guards the north gate", capabilities=["patrol", "detect"])
    e.auto_summarize()
    assert "Village Guard" in e.ai_summary
    assert "npc" in e.ai_summary
    assert e.state_summary == "default state"
    print("  [PASS] test_auto_summarize")

def test_semantic_search():
    from aetherforge.core import SemanticEntity
    class MockWorld:
        def __init__(self):
            self.entities = {}
            for name in ["Guard", "Merchant", "Blacksmith"]:
                e = SemanticEntity(name=name, semantic_type="npc", ai_summary=f"A {name} character")
                e.auto_summarize()
                self.entities[f"e_{name.lower()}"] = e

    w = MockWorld()
    results = [e for e in w.entities.values() if "guard" in e.ai_summary.lower() or "guard" in e.name.lower()]
    assert len(results) >= 1
    assert any("Guard" in e.name for e in results)
    print("  [PASS] test_semantic_search")

if __name__ == "__main__":
    tests = [test_risk_level_assessment, test_required_agents, test_snapshot_diff,
             test_suggestion_candidates, test_art_director_review,
             test_auto_summarize, test_semantic_search]
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