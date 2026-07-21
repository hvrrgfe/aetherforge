"""Scene Test Runner - executes automated tests against scenes/world."""
import json, time, threading
from typing import Optional, Dict, List, Any
from aetherforge.validation.assertions import AssertionEngine, AssertionResult

class SceneTestRunner:
    """Runs automated tests against the world model."""

    def __init__(self, world_model):
        self._world = world_model
        self._assert = AssertionEngine(world_model)

    def run_test_suite(self, tests: List[Dict]) -> Dict:
        """Run a list of test definitions and return results.
        
        Each test: {"name": str, "type": str, "params": dict}
        """
        results = []
        passed = 0
        failed = 0
        for test_def in tests:
            try:
                result = self._run_single_test(test_def)
                results.append(result.to_dict())
                if result.passed:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                results.append({"passed": False, "name": test_def.get("name", "unknown"),
                                "detail": str(e)})
                failed += 1
        return {"total": len(tests), "passed": passed, "failed": failed, "results": results}

    def _run_single_test(self, test_def: Dict) -> AssertionResult:
        ttype = test_def.get("type", "")
        params = test_def.get("params", {})
        if ttype == "entity_exists":
            return self._assert.entity_exists(params.get("entity_id", ""))
        elif ttype == "entity_has_name":
            return self._assert.entity_has_name(params.get("entity_id", ""),
                                                 params.get("name", ""))
        elif ttype == "entity_has_type":
            return self._assert.entity_has_type(params.get("entity_id", ""),
                                                 params.get("type", ""))
        elif ttype == "entity_has_capability":
            return self._assert.entity_has_capability(params.get("entity_id", ""),
                                                       params.get("capability", ""))
        elif ttype == "entity_count_at_least":
            return self._assert.entity_count_at_least(params.get("min", 0))
        elif ttype == "rule_exists":
            return self._assert.rule_exists(params.get("rule_id", ""))
        elif ttype == "quest_exists":
            return self._assert.quest_exists(params.get("quest_id", ""))
        elif ttype == "behavior_assigned":
            return self._assert.behavior_assigned(params.get("entity_id", ""))
        elif ttype == "relationship_exists":
            return self._assert.relationship_exists(
                params.get("entity_id", ""), params.get("type", ""), params.get("target", ""))
        elif ttype == "world_state_ok":
            return self._assert.world_state_ok()
        else:
            return AssertionResult(False, ttype, f"Unknown test type: {ttype}")