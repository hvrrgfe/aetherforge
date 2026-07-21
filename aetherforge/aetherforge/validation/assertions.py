"""Assertion Engine - deterministic checks against world state.

All assertions check real engine state, never model text.
Used by Verifier and InvariantChecker.
"""
from typing import Optional, Dict, List, Any

class AssertionResult:
    """Result of a single assertion check."""
    def __init__(self, passed: bool, name: str = "", detail: str = "",
                 expected: Any = None, actual: Any = None):
        self.passed = passed
        self.name = name
        self.detail = detail
        self.expected = expected
        self.actual = actual

    def to_dict(self) -> dict:
        return {"passed": self.passed, "name": self.name, "detail": self.detail,
                "expected": str(self.expected)[:200], "actual": str(self.actual)[:200]}

class AssertionEngine:
    """Collection of deterministic assertions against WorldModel."""

    def __init__(self, world_model):
        self._world = world_model

    def entity_exists(self, entity_id: str) -> AssertionResult:
        ent = self._world.get_entity(entity_id) if hasattr(self._world, 'get_entity') else None
        if ent is None:
            ent = getattr(self._world, 'entities', {}).get(entity_id)
        passed = ent is not None
        return AssertionResult(passed, "entity_exists",
                               f"Entity {entity_id} {'exists' if passed else 'not found'}",
                               expected=True, actual=passed)

    def entity_has_name(self, entity_id: str, expected_name: str = "") -> AssertionResult:
        ent = self._world.get_entity(entity_id) if hasattr(self._world, 'get_entity') else None
        if ent is None:
            ent = getattr(self._world, 'entities', {}).get(entity_id)
        actual_name = getattr(ent, 'name', '') if ent else ''
        passed = bool(ent) and (not expected_name or actual_name == expected_name)
        return AssertionResult(passed, "entity_has_name",
                               f"Entity {entity_id} name: '{actual_name}'",
                               expected_name, actual_name)

    def entity_has_type(self, entity_id: str, expected_type: str) -> AssertionResult:
        ent = self._world.get_entity(entity_id) if hasattr(self._world, 'get_entity') else None
        if ent is None:
            ent = getattr(self._world, 'entities', {}).get(entity_id)
        actual_type = getattr(ent, 'semantic_type', '') if ent else ''
        passed = bool(ent) and actual_type == expected_type
        return AssertionResult(passed, "entity_has_type",
                               f"Entity {entity_id} type: '{actual_type}'",
                               expected_type, actual_type)

    def entity_has_capability(self, entity_id: str, capability: str) -> AssertionResult:
        ent = self._world.get_entity(entity_id) if hasattr(self._world, 'get_entity') else None
        if ent is None:
            ent = getattr(self._world, 'entities', {}).get(entity_id)
        caps = getattr(ent, 'capabilities', []) if ent else []
        passed = bool(ent) and capability in caps
        return AssertionResult(passed, "entity_has_capability",
                               f"Capability '{capability}' {'found' if passed else 'not found'}",
                               expected=capability, actual=caps)

    def entity_count(self, expected_count: int = 0) -> AssertionResult:
        entities = getattr(self._world, 'entities', {})
        actual = len(entities)
        passed = actual == expected_count if expected_count > 0 else True
        return AssertionResult(passed or False, "entity_count",
                               f"Entity count: {actual}", expected_count, actual)

    def entity_count_at_least(self, min_count: int) -> AssertionResult:
        entities = getattr(self._world, 'entities', {})
        actual = len(entities)
        passed = actual >= min_count
        return AssertionResult(passed, "entity_count_at_least",
                               f"Entity count: {actual} >= {min_count}: {passed}",
                               min_count, actual)

    def rule_exists(self, rule_id: str = "") -> AssertionResult:
        rules = getattr(self._world, 'rules', {})
        if rule_id:
            passed = rule_id in rules
        else:
            passed = len(rules) > 0
        return AssertionResult(passed, "rule_exists",
                               f"Rule exists: {passed}",
                               expected=True, actual=len(rules))

    def quest_exists(self, quest_id: str = "") -> AssertionResult:
        quests = getattr(self._world, 'quests', {})
        if quest_id:
            passed = quest_id in quests
        else:
            passed = len(quests) > 0
        return AssertionResult(passed, "quest_exists",
                               f"Quest exists: {passed}",
                               expected=True, actual=len(quests))

    def behavior_assigned(self, entity_id: str) -> AssertionResult:
        behaviors = getattr(self._world, 'behaviors', {})
        passed = entity_id in behaviors
        return AssertionResult(passed, "behavior_assigned",
                               f"Behavior for {entity_id}: {passed}")

    def relationship_exists(self, entity_id: str, rel_type: str = "",
                            target_id: str = "") -> AssertionResult:
        ent = self._world.get_entity(entity_id) if hasattr(self._world, 'get_entity') else None
        if ent is None:
            ent = getattr(self._world, 'entities', {}).get(entity_id)
        rels = getattr(ent, 'relationships', []) if ent else []
        passed = False
        for r in rels:
            rtype = r.get('type', '') if isinstance(r, dict) else getattr(r, 'type', '')
            rtarget = r.get('target', '') if isinstance(r, dict) else getattr(r, 'target', '')
            if (not rel_type or rtype == rel_type) and (not target_id or rtarget == target_id):
                passed = True
                break
        return AssertionResult(passed, "relationship_exists",
                               f"Relationship {rel_type}->{target_id} for {entity_id}: {passed}")

    def world_state_ok(self) -> AssertionResult:
        """Check world state is internally consistent."""
        entities = getattr(self._world, 'entities', {})
        player_id = getattr(self._world, 'player_entity_id', None)
        issues = []
        if player_id and player_id not in entities:
            issues.append(f"Player {player_id} not in entities")
        passed = len(issues) == 0
        return AssertionResult(passed, "world_state_ok",
                               f"World state issues: {issues}" if issues else "World state OK")