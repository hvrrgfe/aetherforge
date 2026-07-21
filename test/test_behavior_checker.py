"""Tests for validation/behavior_checker.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

def test_behavior_valid():
    from aetherforge.validation.behavior_checker import BehaviorChecker

    class MockEntity:
        entity_id = "guard"
        name = "Guard"
        waypoints = [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]

    class MockWorld:
        entities = {"guard": MockEntity()}
        behaviors = {"guard": ["patrol"]}

    bc = BehaviorChecker()
    result = bc.check_entity_behavior("guard", "patrol", MockWorld())
    assert result.valid
    print("  [PASS] test_behavior_valid")

def test_behavior_missing_waypoints():
    from aetherforge.validation.behavior_checker import BehaviorChecker

    class MockEntity:
        entity_id = "guard"
        name = "Guard"
        waypoints = [{"x": 0, "y": 0}]

    class MockWorld:
        entities = {"guard": MockEntity()}
        behaviors = {"guard": ["patrol"]}

    bc = BehaviorChecker()
    result = bc.check_entity_behavior("guard", "patrol", MockWorld())
    assert not result.valid
    print("  [PASS] test_behavior_missing_waypoints")

def test_behavior_not_bound():
    from aetherforge.validation.behavior_checker import BehaviorChecker

    class MockWorld:
        entities = {"guard": type("E", (), {"entity_id": "guard", "name": "Guard"})()}
        behaviors = {}

    bc = BehaviorChecker()
    result = bc.check_entity_behavior("guard", "patrol", MockWorld())
    assert not result.valid
    print("  [PASS] test_behavior_not_bound")

if __name__ == "__main__":
    for t in [test_behavior_valid, test_behavior_missing_waypoints, test_behavior_not_bound]:
        try:
            t()
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")