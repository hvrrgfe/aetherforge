"""Suggestion System - human feedback as structured objects.

Supports creation of human suggestions, auto-generation of candidate
implementation plans, and matching suggestions to tasks.
"""
import uuid, time, json
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class SuggestionStatus(str, Enum):
    PROPOSED = "proposed"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"

class Candidate:
    """A candidate implementation plan for a suggestion."""

    def __init__(self, label: str, description: str, changes: List[Dict],
                 impact: str = "medium", risk: str = "low",
                 token_estimate: int = 1000):
        self.id = f"cand_{uuid.uuid4().hex[:8]}"
        self.label = label
        self.description = description
        self.changes = changes
        self.impact = impact
        self.risk = risk
        self.token_estimate = token_estimate

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "label": self.label,
            "description": self.description, "impact": self.impact,
            "risk": self.risk, "token_estimate": self.token_estimate,
            "change_count": len(self.changes),
        }

class Suggestion:
    """A structured human suggestion or feedback."""

    def __init__(self, author: str, target: Dict, content: str,
                 intent: str = "", constraints: List[str] = None):
        self.id = f"sug_{uuid.uuid4().hex[:8]}"
        self.author = author
        self.target = target
        self.content = content
        self.intent = intent
        self.constraints = constraints or []
        self.status = SuggestionStatus.PROPOSED
        self.created_at = datetime.utcnow()
        self.candidates: List[Candidate] = []

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "author": self.author,
            "target": self.target, "content": self.content,
            "intent": self.intent, "constraints": self.constraints,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() + "Z",
            "candidates": [c.to_dict() for c in self.candidates],
        }

class SuggestionManager:
    """Manages suggestions and candidate generation."""

    def __init__(self):
        self._suggestions: Dict[str, Suggestion] = {}

    def create_suggestion(self, author: str, target: Dict,
                          content: str, intent: str = "",
                          constraints: List[str] = None) -> Suggestion:
        """Create a new suggestion."""
        sug = Suggestion(author, target, content, intent, constraints)
        self._suggestions[sug.id] = sug
        return sug

    def generate_candidates(self, suggestion: Suggestion) -> List[Candidate]:
        """Generate candidate implementation approaches.

        Produces 2-3 candidate plans with different tradeoffs.
        """
        if suggestion.candidates:
            return suggestion.candidates

        target_type = suggestion.target.get("type", "unknown")
        content = suggestion.content

        # Generate scheme A: Minimal
        cand_a = Candidate(
            label="方案A：最小实现",
            description=f"仅实现核心需求：{content[:80]}",
            changes=[{"op": "modify", "target": suggestion.target, "reason": "core requirement"}],
            impact="low", risk="low", token_estimate=500,
        )
        suggestion.candidates.append(cand_a)

        # Generate scheme B: Balanced
        cand_b = Candidate(
            label="方案B：平衡实现",
            description=f"实现核心需求并补充相关内容：{content[:80]}",
            changes=[{"op": "modify", "target": suggestion.target, "reason": "core"},
                     {"op": "enhance", "target": suggestion.target, "reason": "polish"}],
            impact="medium", risk="low", token_estimate=1500,
        )
        suggestion.candidates.append(cand_b)

        # Generate scheme C: Comprehensive
        if target_type in ("scene", "entity", "quest"):
            cand_c = Candidate(
                label="方案C：完整实现",
                description=f"完整实现{target_type}需求及相关配套：{content[:60]}",
                changes=[{"op": "modify", "target": suggestion.target, "reason": "core"},
                         {"op": "create", "target": {"type": "related"}, "reason": "supporting"},
                         {"op": "enhance", "target": suggestion.target, "reason": "quality"}],
                impact="high", risk="medium", token_estimate=3000,
            )
            suggestion.candidates.append(cand_c)

        return suggestion.candidates

    def accept_suggestion(self, sug_id: str, candidate_id: str = "") -> Dict:
        """Accept a suggestion (optionally with a specific candidate)."""
        sug = self._suggestions.get(sug_id)
        if not sug:
            return {"success": False, "error": f"Suggestion {sug_id} not found"}
        sug.status = SuggestionStatus.ACCEPTED
        result = {"suggestion_id": sug_id, "status": "accepted"}
        if candidate_id:
            result["candidate_id"] = candidate_id
        return result

    def get_suggestion(self, sug_id: str) -> Optional[Suggestion]:
        return self._suggestions.get(sug_id)

    def get_all(self, status: str = "") -> List[Dict]:
        results = []
        for sug in self._suggestions.values():
            if status and sug.status.value != status:
                continue
            results.append(sug.to_dict())
        return results

    def to_dict(self) -> Dict:
        return {"count": len(self._suggestions)}