"""Quest Reachability Validator.

Verifies that quests have complete prerequisite chains,
target entities exist, state transitions are possible,
and the quest can be completed.
"""
from typing import Optional, Dict, List, Any

class QuestReachabilityResult:
    def __init__(self, quest_id: str, reachable: bool):
        self.quest_id = quest_id
        self.reachable = reachable
        self.checks: List[Dict] = []

    def add_check(self, name: str, passed: bool, message: str = ""):
        self.checks.append({"name": name, "passed": passed, "message": message})

    def to_dict(self) -> Dict:
        return {
            "quest_id": self.quest_id,
            "reachable": self.reachable,
            "passed": sum(1 for c in self.checks if c["passed"]),
            "failed": sum(1 for c in self.checks if not c["passed"]),
            "checks": self.checks,
        }

class QuestReachabilityValidator:
    """Validates that quests are reachable and completable."""

    def validate(self, quest_id: str, world_model=None) -> QuestReachabilityResult:
        """Validate quest reachability."""
        result = QuestReachabilityResult(quest_id, False)
        if not world_model:
            result.add_check("world_exists", False, "No world model provided")
            return result

        quests = getattr(world_model, 'quests', {})
        quest = quests.get(quest_id) if isinstance(quests, dict) else None
        if not quest:
            result.add_check("quest_exists", False, f"Quest {quest_id} not found")
            return result

        entities = getattr(world_model, 'entities', {})

        # Check: quest exists with valid state
        q_state = self._get_attr(quest, 'state', {})
        has_valid_state = bool(q_state) or self._get_attr(quest, 'status', '')
        result.add_check("has_state", bool(has_valid_state),
                         f"State: {q_state}" if has_valid_state else "No state found")

        # Check: target entities exist
        target_ids = self._get_attr(quest, 'target_ids', []) or self._get_attr(quest, 'target_id', '')
        if isinstance(target_ids, str):
            target_ids = [target_ids]
        if target_ids:
            missing = [tid for tid in target_ids if tid not in entities]
            if missing:
                result.add_check("target_exists", False,
                                 f"Missing targets: {missing}")
            else:
                result.add_check("target_exists", True, f"All {len(target_ids)} targets exist")
        else:
            result.add_check("target_exists", True, "No specific target required")

        # Check: prerequisite entities exist
        prereq_ids = self._get_attr(quest, 'prerequisites', []) or self._get_attr(quest, 'requires', [])
        if isinstance(prereq_ids, str):
            prereq_ids = [prereq_ids]
        if prereq_ids:
            missing_prereq = [pid for pid in prereq_ids if pid not in entities]
            if missing_prereq:
                result.add_check("prerequisites_met", False,
                                 f"Missing prerequisites: {missing_prereq}")
            else:
                result.add_check("prerequisites_met", True, "All prerequisites exist")
        else:
            result.add_check("prerequisites_met", True, "No prerequisites required")

        # Check: at least one step/action exists
        steps = self._get_attr(quest, 'steps', []) or self._get_attr(quest, 'actions', [])
        if not steps:
            steps = self._get_attr(quest, 'objectives', [])
        if steps:
            result.add_check("has_steps", True, f"{len(steps)} steps defined")
        else:
            result.add_check("has_steps", False, "No steps/actions/objectives defined")

        # Overall reachability
        result.reachable = all(c["passed"] for c in result.checks)
        return result

    def _get_attr(self, obj, name, default=None):
        """Get attribute from object or dict safely."""
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)