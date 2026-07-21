"""Tests for validation/quest_reachability.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

def test_quest_reachable():
    from aetherforge.validation.quest_reachability import QuestReachabilityValidator
    from aetherforge.core import Quest, SemanticEntity

    class MockWorld:
        def __init__(self):
            self.entities = {"knight": SemanticEntity(entity_id="knight", name="Knight", semantic_type="npc")}
            self.quests = {}
            q = Quest(quest_id="q1", name="Test Quest", state="active")
            q.target_ids = ["knight"]
            q.steps = [type("Step", (), {"step_id": "s1", "description": "Talk to knight", "condition": "talk_done"})]
            self.quests["q1"] = q

    val = QuestReachabilityValidator()
    result = val.validate("q1", MockWorld())
    assert result.reachable
    print("  [PASS] test_quest_reachable")

def test_quest_missing_target():
    from aetherforge.validation.quest_reachability import QuestReachabilityValidator
    from aetherforge.core import Quest

    class MockWorld:
        def __init__(self):
            self.entities = {}
            self.quests = {}
            q = Quest(quest_id="q1", name="Missing Target")
            q.target_ids = ["nonexistent_sword"]
            q.steps = [type("Step", (), {"step_id": "s1", "description": "Find sword"})]
            self.quests["q1"] = q

    val = QuestReachabilityValidator()
    result = val.validate("q1", MockWorld())
    assert not result.reachable
    assert any("Missing targets" in c["message"] for c in result.checks if not c["passed"])
    print("  [PASS] test_quest_missing_target")

def test_quest_not_found():
    from aetherforge.validation.quest_reachability import QuestReachabilityValidator
    val = QuestReachabilityValidator()
    result = val.validate("unknown", type("W", (), {"quests": {}, "entities": {}})())
    assert not result.reachable
    print("  [PASS] test_quest_not_found")

if __name__ == "__main__":
    for t in [test_quest_reachable, test_quest_missing_target, test_quest_not_found]:
        try:
            t()
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")