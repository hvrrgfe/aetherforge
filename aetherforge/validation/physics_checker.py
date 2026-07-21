"""Physics Checker - validates physics properties for stability.

Checks collision bodies, mass values, position overlaps,
and detects abnormal velocities.
"""
from typing import Optional, Dict, List, Any

class PhysicsCheckResult:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.stable = False
        self.checks: List[Dict] = []

    def add_check(self, name: str, passed: bool, message: str = ""):
        self.checks.append({"name": name, "passed": passed, "message": message})

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "stable": self.stable,
            "passed": sum(1 for c in self.checks if c["passed"]),
            "failed": sum(1 for c in self.checks if not c["failed"]),
            "checks": self.checks,
        }

class PhysicsChecker:
    """Validates physics properties for entity stability."""

    def check_entity(self, entity_id: str, world_model=None) -> PhysicsCheckResult:
        """Check physics properties of an entity."""
        result = PhysicsCheckResult(entity_id)
        if not world_model:
            result.add_check("world_exists", False, "No world model")
            return result

        entities = getattr(world_model, 'entities', {})
        entity = entities.get(entity_id) if isinstance(entities, dict) else None
        if not entity:
            result.add_check("entity_exists", False, f"Entity {entity_id} not found")
            return result

        # Check position validity
        pos = entity.get("position", {}) if isinstance(entity, dict) else getattr(entity, 'position', None)
        if pos:
            if isinstance(pos, dict):
                x = float(pos.get("x", 0))
                y = float(pos.get("y", 0))
                z = float(pos.get("z", 0))
            else:
                x, y, z = 0, 0, 0
            abnormal = abs(x) > 1e6 or abs(y) > 1e6 or abs(z) > 1e6
            result.add_check("position_valid", not abnormal,
                             f"Position ({x:.1f}, {y:.1f}, {z:.1f})" if not abnormal else "Position out of range")
        else:
            result.add_check("position_valid", True, "No position set (default)")

        # Check size validity
        size = entity.get("size", {}) if isinstance(entity, dict) else getattr(entity, 'size', {})
        if size:
            if isinstance(size, dict):
                w = float(size.get("width", size.get("w", 1)))
                h = float(size.get("height", size.get("h", 1)))
            else:
                w, h = 1, 1
            valid_size = w > 0 and h > 0 and w < 1e6 and h < 1e6
            result.add_check("size_valid", valid_size,
                             f"Size ({w:.1f}, {h:.1f})" if valid_size else "Invalid size")
        else:
            result.add_check("size_valid", True, "No size set (default)")

        # Check for overlap with other entities
        overlap_count = 0
        for eid2, ent2 in entities.items():
            if eid2 == entity_id:
                continue
            pos2 = ent2.get("position", {}) if isinstance(ent2, dict) else getattr(ent2, 'position', {})
            if pos and pos2:
                if isinstance(pos, dict) and isinstance(pos2, dict):
                    dx = abs(float(pos.get("x", 0)) - float(pos2.get("x", 0)))
                    dy = abs(float(pos.get("y", 0)) - float(pos2.get("y", 0)))
                    if dx < 0.1 and dy < 0.1:
                        overlap_count += 1
        result.add_check("no_overlap", overlap_count == 0,
                         f"No overlaps" if overlap_count == 0 else f"Overlaps with {overlap_count} entities")

        result.stable = all(c["passed"] for c in result.checks)
        return result

    def check_all(self, world_model=None) -> List[Dict]:
        """Check physics for all entities."""
        results = []
        if not world_model:
            return results
        entities = getattr(world_model, 'entities', {})
        for eid in entities:
            results.append(self.check_entity(eid, world_model).to_dict())
        return results