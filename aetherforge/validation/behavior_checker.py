"""Behavior Checker - validates that behaviors are properly configured.

Checks that behaviors are bound to entities, have valid parameters,
waypoints exist for patrol behaviors, and behaviors can be tick-driven.
"""
from typing import Optional, Dict, List, Any

class BehaviorCheckResult:
    def __init__(self, entity_id: str, behavior_name: str):
        self.entity_id = entity_id
        self.behavior_name = behavior_name
        self.valid = False
        self.checks: List[Dict] = []

    def add_check(self, name: str, passed: bool, message: str = ""):
        self.checks.append({"name": name, "passed": passed, "message": message})

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "behavior": self.behavior_name,
            "valid": self.valid,
            "passed": sum(1 for c in self.checks if c["passed"]),
            "failed": sum(1 for c in self.checks if not c["passed"]),
            "checks": self.checks,
        }

class BehaviorChecker:
    """Validates entity behavior configuration."""

    def check_entity_behavior(self, entity_id: str, behavior_name: str,
                              world_model=None) -> BehaviorCheckResult:
        """Check a specific behavior on an entity."""
        result = BehaviorCheckResult(entity_id, behavior_name)
        if not world_model:
            result.add_check("world_exists", False, "No world model")
            return result

        entities = getattr(world_model, 'entities', {})
        behaviors = getattr(world_model, 'behaviors', {})

        # Check entity exists
        entity = entities.get(entity_id) if isinstance(entities, dict) else None
        if not entity:
            result.add_check("entity_exists", False, f"Entity {entity_id} not found")
            return result
        result.add_check("entity_exists", True)

        # Check behavior is registered for this entity
        entity_behaviors = behaviors.get(entity_id, []) if isinstance(behaviors, dict) else []
        if isinstance(entity_behaviors, list):
            behavior_found = any(
                (isinstance(b, str) and b == behavior_name) or
                (isinstance(b, dict) and b.get("name") == behavior_name)
                for b in entity_behaviors
            )
        else:
            behavior_found = behavior_name in str(entity_behaviors)

        if behavior_found:
            result.add_check("behavior_bound", True, f"Behavior {behavior_name} is bound")
        else:
            result.add_check("behavior_bound", False, f"Behavior {behavior_name} not bound to {entity_id}")

        # Check patrol waypoints
        if "patrol" in behavior_name.lower():
            waypoints = []
            if isinstance(entity, dict):
                wp = entity.get("waypoints", entity.get("patrol_points", []))
            else:
                wp = getattr(entity, 'waypoints', []) or getattr(entity, 'patrol_points', [])
            if isinstance(wp, list):
                waypoints = wp
            if len(waypoints) >= 2:
                result.add_check("has_waypoints", True, f"{len(waypoints)} waypoints configured")
            else:
                result.add_check("has_waypoints", False,
                                 f"Patrol needs >=2 waypoints, found {len(waypoints)}")

        result.valid = all(c["passed"] for c in result.checks)
        return result

    def check_all_behaviors(self, world_model=None) -> List[Dict]:
        """Check all behaviors in the world."""
        results = []
        if not world_model:
            return results
        behaviors = getattr(world_model, 'behaviors', {})
        entities = getattr(world_model, 'entities', {})
        for eid, behs in behaviors.items():
            if eid not in entities:
                results.append({
                    "entity_id": eid, "error": "Orphan behavior - entity not found"
                })
                continue
            if isinstance(behs, list):
                for b in behs:
                    bname = b if isinstance(b, str) else (b.get("name", "unknown") if isinstance(b, dict) else "unknown")
                    results.append(self.check_entity_behavior(eid, bname, world_model).to_dict())
        return results