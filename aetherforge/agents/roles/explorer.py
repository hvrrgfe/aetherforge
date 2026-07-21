"""Explorer Agent - read-only world exploration.

Gathers facts, finds unknowns, and identifies constraints.
Never modifies world state.
"""
import uuid, json, time
from typing import Optional, Dict, List, Any

class BaseAgentRole:
    def __init__(self, gateway, evidence_store=None, state_manager=None):
        self.gateway = gateway
        self.evidence = evidence_store
        self.state_mgr = state_manager
        self.role = None

class Explorer(BaseAgentRole):
    """Read-only explorer that gathers facts about the world."""

    def __init__(self, gateway, evidence_store=None, state_manager=None):
        super().__init__(gateway, evidence_store, state_manager)
        self.role = "explorer"
        self._facts = []
        self._unknowns = []
        self._constraints = []

    def explore(self, entity_type="", tags=None) -> Dict:
        """Explore the world and return structured facts."""
        self._facts = []
        self._unknowns = []
        self._constraints = []

        # Observe world state
        obs = self.gateway.observe()
        if obs.get("success"):
            self._facts.append({
                "content": f"World observed",
                "source": {"tool": "observe", "call_id": f"exp_{int(time.time()*1000)}"},
            })

        # Find entities by type
        if entity_type:
            result = self.gateway.find_entities(query=entity_type)
            if result.get("success"):
                count = result.get("data", {}).get("count", 0)
                self._facts.append({
                    "content": f"Found {count} entities of type '{entity_type}'",
                    "source": {"tool": "find_entities", "call_id": f"exp_{int(time.time()*1000)}"},
                })

        # Check for active transaction
        if self.state_mgr:
            rev = self.state_mgr.world_revision
            self._facts.append({
                "content": f"World revision: {rev}",
                "source": {"tool": "state_manager", "call_id": "internal"},
            })
            active = self.state_mgr.active_task
            if active:
                self._constraints.append({
                    "content": f"Active task: {active.task_id} in phase {active.phase.value if hasattr(active.phase, 'value') else active.phase}"
                })

        return self._build_report()

    def _build_report(self) -> Dict:
        return {
            "facts": self._facts,
            "unknowns": self._unknowns,
            "constraints": self._constraints,
            "fact_count": len(self._facts),
            "unknown_count": len(self._unknowns),
            "constraint_count": len(self._constraints),
        }

    def add_fact(self, content: str, tool: str = "manual") -> None:
        self._facts.append({
            "content": content,
            "source": {"tool": tool, "call_id": f"exp_{int(time.time()*1000)}"},
        })

    def add_unknown(self, content: str) -> None:
        self._unknowns.append({"content": content})

    def add_constraint(self, content: str) -> None:
        self._constraints.append({"content": content})

    def to_dict(self) -> Dict:
        return {"role": self.role, "facts": len(self._facts),
                "unknowns": len(self._unknowns), "constraints": len(self._constraints)}