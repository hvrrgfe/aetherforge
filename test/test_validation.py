"""Tests for Validation subsystem (assertions, scene tests, invariants, consistency)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aetherforge.validation.assertions import AssertionEngine
from aetherforge.validation.scene_tests import SceneTestRunner
from aetherforge.validation.invariants import InvariantChecker
from aetherforge.validation.consistency import ConsistencyValidator

class MockWorld:
    def __init__(self):
        self.entities = {}
        self.rules = {}
        self.quests = {}
        self.behaviors = {}
        self.player_entity_id = None

    def get_entity(self, eid):
        return self.entities.get(eid)

def make_entity(eid, name="", stype="", caps=None, rels=None):
    return type("Entity", (), {
        "entity_id": eid, "name": name, "semantic_type": stype,
        "capabilities": caps or [], "relationships": rels or [],
        "state": {}, "position": {"x": 0, "y": 0},
    })()

# --- Assertion Tests ---

def test_entity_exists():
    world = MockWorld()
    ae = AssertionEngine(world)
    r = ae.entity_exists("nonexistent")
    assert not r.passed
    world.entities["ent_1"] = make_entity("ent_1", "Guard")
    r = ae.entity_exists("ent_1")
    assert r.passed
    print("  [PASS] entity_exists")

def test_entity_has_name():
    world = MockWorld()
    world.entities["e1"] = make_entity("e1", "Village Guard")
    ae = AssertionEngine(world)
    assert ae.entity_has_name("e1", "Village Guard").passed
    assert not ae.entity_has_name("e1", "Wrong Name").passed
    print("  [PASS] entity_has_name")

def test_entity_has_type():
    world = MockWorld()
    world.entities["e1"] = make_entity("e1", stype="npc")
    ae = AssertionEngine(world)
    assert ae.entity_has_type("e1", "npc").passed
    assert not ae.entity_has_type("e1", "item").passed
    print("  [PASS] entity_has_type")

def test_entity_has_capability():
    world = MockWorld()
    world.entities["e1"] = make_entity("e1", caps=["move", "talk"])
    ae = AssertionEngine(world)
    assert ae.entity_has_capability("e1", "talk").passed
    assert not ae.entity_has_capability("e1", "fly").passed
    print("  [PASS] entity_has_capability")

def test_entity_count():
    world = MockWorld()
    world.entities["e1"] = make_entity("e1")
    world.entities["e2"] = make_entity("e2")
    ae = AssertionEngine(world)
    r = ae.entity_count_at_least(2)
    assert r.passed
    r = ae.entity_count_at_least(3)
    assert not r.passed
    print("  [PASS] entity_count")

# --- Scene Test Runner ---

def test_scene_runner():
    world = MockWorld()
    world.entities["e1"] = make_entity("e1", "Guard", "npc")
    runner = SceneTestRunner(world)
    tests = [
        {"name": "Guard exists", "type": "entity_exists", "params": {"entity_id": "e1"}},
        {"name": "Guard is NPC", "type": "entity_has_type", "params": {"entity_id": "e1", "type": "npc"}},
        {"name": "Missing entity", "type": "entity_exists", "params": {"entity_id": "e99"}},
    ]
    result = runner.run_test_suite(tests)
    assert result["total"] == 3
    assert result["passed"] == 2
    assert result["failed"] == 1
    print(f"  [PASS] scene_runner: {result['passed']}/{result['total']}")

# --- Invariant Tests ---

def test_invariant_checker():
    world = MockWorld()
    world.entities["e1"] = make_entity("e1")
    world.behaviors["e1"] = {"type": "patrol"}
    world.behaviors["e_orphan"] = {"type": "wander"}  # orphan - no entity
    ic = InvariantChecker(world)
    result = ic.check_all()
    assert result["failed"] >= 1  # orphan behavior
    print(f"  [PASS] invariant_checker: {result['passed']}/{result['total']}")

def test_consistency_validator():
    world = MockWorld()
    world.entities["g1"] = make_entity("g1", "Guard", "npc")
    world.entities["g2"] = make_entity("g2", "Guard", "npc")  # duplicate name
    cv = ConsistencyValidator(world)
    result = cv.validate_all()
    assert result["failed"] >= 1  # duplicate names
    print(f"  [PASS] consistency_validator: {result['passed']}/{result['total']}")

if __name__ == "__main__":
    tests = [test_entity_exists, test_entity_has_name, test_entity_has_type,
             test_entity_has_capability, test_entity_count, test_scene_runner,
             test_invariant_checker, test_consistency_validator]
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