"""Critic Agent - adversarial review and security checking.

READ-ONLY role. Finds issues that Verifier might have missed.
"""
import uuid, time
from typing import Optional, Dict, List, Any
from aetherforge.agents.roles.explorer import BaseAgentRole

class Critic(BaseAgentRole):
    """Adversarial reviewer that finds issues and edge cases."""

    def __init__(self, gateway, evidence_store=None, state_manager=None):
        super().__init__(gateway, evidence_store, state_manager)
        self.role = "critic"
        self._issues = []

    def review(self, task_id: str, world_model=None) -> Dict:
        """Review world state for issues."""
        self._issues = []

        entities = getattr(world_model, 'entities', {}) if world_model else {}

        # Check for potential issues
        self._check_entity_integrity(entities)
        self._check_security_policies()
        self._check_edge_cases(entities)

        blocking = [i for i in self._issues if i.get("severity") in ("critical", "high")]
        return {
            "task_id": task_id,
            "total_issues": len(self._issues),
            "blocking": len(blocking),
            "issues": self._issues,
        }

    def _check_entity_integrity(self, entities: Dict) -> None:
        """Check entities for integrity issues."""
        for eid, ent in entities.items():
            name = getattr(ent, 'name', '') if not isinstance(ent, dict) else ent.get('name', '')
            if not name:
                self._issues.append({
                    "severity": "medium",
                    "description": f"Entity {eid} has no name",
                    "category": "integrity",
                    "repairable": True,
                    "entity_id": eid,
                })

    def _check_security_policies(self) -> None:
        """Check security policies."""
        pass  # Extensible for security rules

    def _check_edge_cases(self, entities: Dict) -> None:
        """Check for edge cases."""
        if len(entities) == 0:
            self._issues.append({
                "severity": "high",
                "description": "World has no entities",
                "category": "edge_case",
                "repairable": True,
            })
        elif len(entities) == 1:
            self._issues.append({
                "severity": "low",
                "description": "World has only one entity",
                "category": "edge_case",
                "repairable": True,
            })


    def generate_repair_plan(self, issues):
        """Generate repair steps for fixable issues."""
        repairs = []
        for issue in issues:
            if not issue.get("repairable", False):
                continue
            desc = issue.get("description", "")
            if "no name" in desc:
                repairs.append({
                    "target": issue.get("entity_id", ""),
                    "action": "set_name",
                    "suggestion": "Assign a descriptive name",
                    "tool": "modify_entity",
                    "params": {"entity_id": issue.get("entity_id", ""),
                              "changes": {"name": "Unnamed Entity"}},
                })
            elif "no entities" in desc:
                repairs.append({
                    "action": "create_default",
                    "suggestion": "Create an initial entity",
                    "tool": "create_entity",
                    "params": {"name": "Starting Area", "semantic_type": "area"},
                })
        return repairs
    def to_dict(self) -> Dict:
        return {"role": self.role, "issues": len(self._issues)}