"""Planner Agent - creates execution plans from Explorer output.

READ-ONLY role that produces structured, verifiable plans.
"""
import uuid, time
from typing import Optional, Dict, List, Any
from aetherforge.agents.roles.explorer import BaseAgentRole
from aetherforge.agents.protocol import AcceptanceCriterion

class Planner(BaseAgentRole):
    """Creates structured execution plans based on world exploration."""

    def __init__(self, gateway, evidence_store=None, state_manager=None):
        super().__init__(gateway, evidence_store, state_manager)
        self.role = "planner"

    def create_plan(self, explorer_output: Dict, goal: str = "") -> Dict:
        """Create an execution plan from explorer output and goal."""
        steps = []
        criteria = []

        # Determine what needs to be done
        constraints = explorer_output.get("constraints", [])
        facts = explorer_output.get("facts", [])

        # Add plan metadata
        plan = {
            "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
            "goal": goal,
            "created_at": time.time(),
            "steps": steps,
            "acceptance_criteria": criteria,
            "estimated_steps": 0,
            "constraints": constraints,
        }

        return plan

    def add_step(self, plan: Dict, action: str, tool: str,
                 params: Dict = None, verification: List[str] = None) -> Dict:
        """Add a step to the plan."""
        step = {
            "step_id": f"step_{len(plan['steps']) + 1}",
            "action": action,
            "tool": tool,
            "params": params or {},
            "verification": verification or [],
        }
        plan["steps"].append(step)
        plan["estimated_steps"] = len(plan["steps"])
        return plan

    def add_criterion(self, plan: Dict, description: str,
                      verification_tool: str = "", params: Dict = None) -> Dict:
        """Add an acceptance criterion to the plan."""
        criterion = AcceptanceCriterion(
            description=description,
            verification_tool=verification_tool,
            verification_params=params or {},
        )
        plan["acceptance_criteria"].append(criterion)
        return plan

    def to_dict(self) -> Dict:
        return {"role": self.role}