"""Consistency Validator - checks semantic consistency of the world.

Validates relationships, data integrity, and business rules.
"""
from typing import Dict, List, Any
from aetherforge.validation.assertions import AssertionResult

class ConsistencyValidator:
    """Validates semantic consistency of the world model."""

    def __init__(self, world_model):
        self._world = world_model

    def validate_all(self) -> Dict:
        """Run all consistency checks."""
        results = []
        results.append(self._check_duplicate_entities())
        results.append(self._check_empty_entities())
        results.append(self._check_circular_relationships())
        results.append(self._check_orphaned_resources())
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        return {"total": len(results), "passed": passed, "failed": failed,
                "results": [r.to_dict() for r in results]}

    def _check_duplicate_entities(self) -> AssertionResult:
        """Check for entities with the same name."""
        entities = getattr(self._world, 'entities', {})
        names = {}
        for eid, ent in entities.items():
            name = getattr(ent, 'name', '') if not isinstance(ent, dict) else ent.get('name', '')
            if name:
                names.setdefault(name, []).append(eid)
        dupes = {n: eids for n, eids in names.items() if len(eids) > 1}
        passed = len(dupes) == 0
        return AssertionResult(passed, "duplicate_entities",
                               f"{len(dupes)} duplicate names" if dupes else "No duplicate names",
                               actual=dupes)

    def _check_empty_entities(self) -> AssertionResult:
        """Check for entities with no name or type."""
        entities = getattr(self._world, 'entities', {})
        empty = []
        for eid, ent in entities.items():
            name = getattr(ent, 'name', '') if not isinstance(ent, dict) else ent.get('name', '')
            stype = getattr(ent, 'semantic_type', '') if not isinstance(ent, dict) else ent.get('semantic_type', '')
            if not name and not stype:
                empty.append(eid)
        passed = len(empty) == 0
        return AssertionResult(passed, "empty_entities",
                               f"{len(empty)} empty entities" if empty else "No empty entities",
                               actual=empty)

    def _check_circular_relationships(self) -> AssertionResult:
        """Check for circular relationships (A contains B contains A)."""
        entities = getattr(self._world, 'entities', {})
        visited = set()
        circular = []

        def dfs(eid, path):
            if eid in path:
                cycle_start = path.index(eid)
                circular.append(path[cycle_start:])
                return
            if eid in visited:
                return
            visited.add(eid)
            ent = entities.get(eid)
            if ent:
                rels = getattr(ent, 'relationships', []) if not isinstance(ent, dict) else ent.get('relationships', [])
                for r in rels:
                    target = r.get('target', '') if isinstance(r, dict) else getattr(r, 'target', '')
                    if target and target in entities:
                        dfs(target, path + [eid])

        for eid in entities:
            if eid not in visited:
                dfs(eid, [])
        passed = len(circular) == 0
        return AssertionResult(passed, "circular_relationships",
                               f"{len(circular)} circular refs" if circular else "No circular refs",
                               actual=circular)

    def _check_orphaned_resources(self) -> AssertionResult:
        """Check for generated assets that aren't referenced."""
        passed = True
        return AssertionResult(passed, "orphaned_resources", "Resource check not yet implemented")