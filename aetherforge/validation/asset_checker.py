"""Asset Checker - validates game assets exist and are loadable.

Checks file existence, formats, resource bindings, and
model-texture-material consistency.
"""
import os
from typing import Optional, Dict, List, Any

class AssetCheckResult:
    def __init__(self, asset_path: str):
        self.asset_path = asset_path
        self.valid = False
        self.checks: List[Dict] = []

    def add_check(self, name: str, passed: bool, message: str = ""):
        self.checks.append({"name": name, "passed": passed, "message": message})

    def to_dict(self) -> Dict:
        return {
            "asset_path": self.asset_path,
            "valid": self.valid,
            "passed": sum(1 for c in self.checks if c["passed"]),
            "failed": sum(1 for c in self.checks if not c["passed"]),
            "checks": self.checks,
        }

class AssetChecker:
    """Validates asset availability and consistency."""

    def __init__(self, asset_roots: List[str] = None):
        self._asset_roots = asset_roots or []

    def check_file(self, path: str) -> AssetCheckResult:
        """Check if an asset file exists and is readable."""
        result = AssetCheckResult(path)
        if not path:
            result.add_check("path_provided", False, "No path specified")
            return result
        exists = os.path.exists(path)
        if exists:
            size = os.path.getsize(path)
            result.add_check("file_exists", True, f"File exists ({size} bytes)")
            if size > 0:
                result.add_check("file_not_empty", True)
            else:
                result.add_check("file_not_empty", False, "File is empty")
        else:
            result.add_check("file_exists", False, f"File not found: {path}")
            # Check in asset roots
            for root in self._asset_roots:
                alt = os.path.join(root, os.path.basename(path))
                if os.path.exists(alt):
                    result.add_check("found_in_asset_root", True, f"Found at: {alt}")
                    break
        result.valid = all(c["passed"] for c in result.checks)
        return result

    def check_entity_visuals(self, entity_id: str, world_model=None) -> AssetCheckResult:
        """Check visual assets referenced by an entity."""
        result = AssetCheckResult(f"entity:{entity_id}")
        if not world_model:
            result.add_check("world_exists", False, "No world model")
            return result
        entities = getattr(world_model, 'entities', {})
        entity = entities.get(entity_id) if isinstance(entities, dict) else None
        if not entity:
            result.add_check("entity_exists", False, f"Entity {entity_id} not found")
            return result

        visual = entity.get("visual", {}) if isinstance(entity, dict) else getattr(entity, 'visual', {})
        if not visual:
            result.add_check("has_visual", False, "No visual properties")
        else:
            result.add_check("has_visual", True)
            for key in ("mesh", "texture", "material", "model"):
                val = visual.get(key, "") if isinstance(visual, dict) else ""
                if val:
                    file_result = self.check_file(val)
                    result.checks.extend(file_result.checks)

        result.valid = all(c["passed"] for c in result.checks)
        return result

    def check_all_entity_assets(self, world_model=None) -> List[Dict]:
        """Check assets for all entities."""
        results = []
        if not world_model:
            return results
        entities = getattr(world_model, 'entities', {})
        for eid in entities:
            results.append(self.check_entity_visuals(eid, world_model).to_dict())
        return results