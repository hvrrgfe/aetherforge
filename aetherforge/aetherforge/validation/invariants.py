"""Invariant Checker - ensures world state invariants are maintained.

Invariants are rules that must ALWAYS be true for the world to be consistent.
"""
from typing import Dict, List, Any
from aetherforge.validation.assertions import AssertionResult

class InvariantChecker:
    """Checks world invariants that must always hold."""

    def __init__(self, world_model):
        self._world = world_model

    def check_all(self) -> Dict:
        """Run all invariant checks."""
        results = []
        results.append(self._check_entity_references())
        results.append(self._check_quest_references())
        results.append(self._check_behavior_references())
        results.append(self._check_player_exists())
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        return {"total": len(results), "passed": passed, "failed": failed,
                "results": [r.to_dict() for r in results]}

    def _check_entity_references(self) -> AssertionResult:
        """All entity relationships reference valid entities."""
        entities = getattr(self._world, 'entities', {})
        issues = []
        for eid, ent in entities.items():
            rels = getattr(ent, 'relationships', []) if not isinstance(ent, dict) else ent.get('relationships', [])
            for r in rels:
                target = r.get('target', '') if isinstance(r, dict) else getattr(r, 'target', '')
                if target and target not in entities:
                    issues.append(f"{eid} -> {target} (missing)")
        passed = len(issues) == 0
        return AssertionResult(passed, "entity_references",
                               f"{len(issues)} broken references" if issues else "All references valid",
                               actual=issues)

    def _check_quest_references(self) -> AssertionResult:
        """All quest steps reference valid entities."""
        quests = getattr(self._world, 'quests', {})
        entities = getattr(self._world, 'entities', {})
        issues = []
        for qid, quest in quests.items():
            steps = getattr(quest, 'steps', []) if not isinstance(quest, dict) else quest.get('steps', [])
            for step in steps:
                target = step.get('target_entity', '') if isinstance(step, dict) else getattr(step, 'target_entity', '')
                if target and target not in entities:
                    issues.append(f"Quest {qid} step targets {target} (missing)")
        passed = len(issues) == 0
        return AssertionResult(passed, "quest_references",
                               f"{len(issues)} broken quest refs" if issues else "All quest refs valid",
                               actual=issues)

    def _check_behavior_references(self) -> AssertionResult:
        """All behaviors reference valid entities."""
        behaviors = getattr(self._world, 'behaviors', {})
        entities = getattr(self._world, 'entities', {})
        issues = [eid for eid in behaviors if eid not in entities]
        passed = len(issues) == 0
        return AssertionResult(passed, "behavior_references",
                               f"{len(issues)} orphaned behaviors" if issues else "All behaviors valid",
                               actual=issues)

    def _check_player_exists(self) -> AssertionResult:
        """Player entity must exist in entities."""
        pid = getattr(self._world, 'player_entity_id', None)
        entities = getattr(self._world, 'entities', {})
        passed = pid is None or pid in entities
        return AssertionResult(passed, "player_exists",
                               f"Player {pid} {'valid' if passed else 'MISSING'}")