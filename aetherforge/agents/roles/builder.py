"""Builder Agent - executes plan steps by calling engine tools.

WRITE role that modifies world state through the ToolGateway.
Cannot call commit_change/rollback_change directly.
"""
import uuid, time
from typing import Optional, Dict, List, Any
from aetherforge.agents.roles.explorer import BaseAgentRole
from aetherforge.agents.protocol import Claim

class Builder(BaseAgentRole):
    """Executes plan steps to modify world state."""

    def __init__(self, gateway, evidence_store=None, state_manager=None):
        super().__init__(gateway, evidence_store, state_manager)
        self.role = "builder"

    def execute_plan(self, plan: Dict) -> Dict:
        """Execute all steps in a plan."""
        results = []
        passed = 0
        failed = 0

        for step in plan.get("steps", []):
            result = self._execute_step(step)
            results.append(result)
            if result.get("success"):
                passed += 1
            else:
                failed += 1

        return {
            "plan_id": plan.get("plan_id", ""),
            "total_steps": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
        }

    def _execute_step(self, step: Dict) -> Dict:
        """Execute a single plan step via the ToolGateway."""
        tool = step.get("tool", "")
        params = step.get("params", {})

        try:
            result = self.gateway.call_tool(tool, **params)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        return {
            "step_id": step.get("step_id", ""),
            "tool": tool,
            "params": params,
            "success": result.get("success", False),
            "result": result,
        }

    def create_claim(self, content: str, category: str = "general",
                     evidence_ids: List[str] = None, task_id: str = "") -> Claim:
        """Create a claim with evidence for verification."""
        return Claim(
            task_id=task_id,
            agent_id="builder",
            content=content,
            category=category,
            evidence_ids=evidence_ids or [],
        )

    def to_dict(self) -> Dict:
        return {"role": self.role}