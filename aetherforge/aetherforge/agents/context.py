"""Context Manager - builds incremental context for model requests.

Token-optimized: sends summaries instead of full state,
and only sends delta (changes) between steps.
"""
import json, threading
from typing import Optional, Dict, List, Any
from aetherforge.agents.protocol import TaskState, Evidence
from aetherforge.agents.policies import TokenBudget

class ContextManager:
    """Builds model context incrementally to minimize token usage."""

    def __init__(self, world_model=None, token_budget=None):
        self._world = world_model
        self._budget = token_budget or TokenBudget()
        self._context_history: List[str] = []
        self._last_snapshot: Dict = {}
        self._total_tokens = 0

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def budget(self) -> TokenBudget:
        return self._budget

    def build_initial_context(self, task: TaskState) -> str:
        """Build initial context with world summary (not full state)."""
        parts = [self._system_prompt(), self._world_summary(compact=True),
                 f"## Task\nGoal: {task.goal}"]
        ctx = "\n\n".join(parts)
        self._context_history = [ctx]
        self._total_tokens = self._estimate_tokens(ctx)
        return ctx

    def build_incremental_context(self, previous: str, changes: List[Dict] = None,
                                   evidence: List[Evidence] = None) -> str:
        """Build context showing only what changed since last step.

        This is the key token optimization: instead of resending
        the entire world state, we only send the delta.
        """
        parts = [previous]

        if changes:
            change_lines = ["## Changes"]
            for c in changes[-10:]:  # Last 10 changes max
                change_lines.append(f"- {c.get('type', 'change')}: {json.dumps(c.get('details', {}))[:100]}")
            parts.append("\n".join(change_lines))

        if evidence:
            ev_lines = ["## New Evidence"]
            for ev in evidence[-5:]:  # Last 5 evidence items max
                summary = json.dumps(ev.result)[:80] if ev.result else "N/A"
                ev_lines.append(f"- {ev.source_tool}: {summary}")
            parts.append("\n".join(ev_lines))

        ctx = "\n\n".join(parts)
        self._total_tokens = self._estimate_tokens(ctx)
        return ctx

    def build_compact_world_summary(self) -> str:
        """Build a compact summary of the world state (token-optimized).

        Instead of listing every entity in full detail, this creates
        a condensed summary suitable for model context.
        """
        return self._world_summary(compact=True)

    def _system_prompt(self) -> str:
        return ("You are an AI agent in the AetherForge game engine. "
                "Operate on semantic entities with types, capabilities, and relationships. "
                "All actions must be verified through evidence.")

    def _world_summary(self, compact: bool = False) -> str:
        if not self._world:
            return "## World\n(no world loaded)"
        entities = getattr(self._world, 'entities', {})
        rules = getattr(self._world, 'rules', {})
        quests = getattr(self._world, 'quests', {})

        if compact:
            # Compact: counts + entity names only
            names = []
            for eid, ent in entities.items():
                n = getattr(ent, 'name', '') if not isinstance(ent, dict) else ent.get('name', '')
                t = getattr(ent, 'semantic_type', '') if not isinstance(ent, dict) else ent.get('semantic_type', '')
                label = n or eid[:12]
                if t:
                    label += f" ({t})"
                names.append(label)
            name_str = ", ".join(names[:20])
            if len(names) > 20:
                name_str += f" ... and {len(names) - 20} more"
            return (f"## World (compact)\n"
                    f"- Entities: {len(entities)}\n"
                    f"- Rules: {len(rules)}\n"
                    f"- Quests: {len(quests)}\n"
                    f"- {name_str}")
        else:
            return (f"## World\nEntities: {len(entities)}\nRules: {len(rules)}\nQuests: {len(quests)}")

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token)."""
        return len(text) // 4

    def to_dict(self) -> dict:
        return {"total_tokens": self._total_tokens, "budget": self._budget.to_dict()}