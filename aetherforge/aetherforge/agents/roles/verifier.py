"""Verifier Agent - independently verifies claims and criteria.

READ-ONLY role. Re-reads engine state directly instead of trusting builder.
"""
import uuid, time
from typing import Optional, Dict, List, Any
from aetherforge.agents.roles.explorer import BaseAgentRole
from aetherforge.agents.protocol import EvidenceStatus
from aetherforge.validation.assertions import AssertionEngine
from aetherforge.validation.scene_tests import SceneTestRunner

class Verifier(BaseAgentRole):
    """Independently verifies claims by re-reading engine state."""

    def __init__(self, gateway, evidence_store=None, state_manager=None,
                 world_model=None):
        super().__init__(gateway, evidence_store, state_manager)
        self.role = "verifier"
        self._assertion_engine = AssertionEngine(world_model) if world_model else None
        self._scene_runner = SceneTestRunner(world_model) if world_model else None

    def verify_claims(self, claims: List[Dict], task_id: str = "") -> List[Dict]:
        """Verify claims by checking evidence."""
        results = []
        for claim in claims:
            cid = claim.get("claim_id", "")
            # Check if evidence exists and is verified
            evidence_ids = claim.get("evidence_ids", [])
            all_verified = True
            for eid in evidence_ids:
                ev = self.evidence.get_evidence(eid) if self.evidence else None
                if not ev or ev.status != EvidenceStatus.VERIFIED:
                    all_verified = False
                    break
            results.append({
                "claim_id": cid,
                "content": claim.get("content", ""),
                "passed": all_verified,
                "evidence_count": len(evidence_ids),
            })
        return results

    def verify_acceptance_criteria(self, criteria: List) -> List[Dict]:
        """Verify acceptance criteria by running assertions."""
        results = []
        for criterion in criteria:
            passed = False
            detail = ""
            tool = getattr(criterion, 'verification_tool', '') if not isinstance(criterion, dict) else criterion.get('verification_tool', '')
            params = getattr(criterion, 'verification_params', {}) if not isinstance(criterion, dict) else criterion.get('verification_params', {})

            if self._assertion_engine and tool:
                assertion_fn = getattr(self._assertion_engine, tool, None)
                if assertion_fn:
                    try:
                        ar = assertion_fn(**params)
                        passed = ar.passed
                        detail = ar.detail
                    except Exception as e:
                        detail = str(e)

            cid = getattr(criterion, 'criterion_id', '') if not isinstance(criterion, dict) else criterion.get('criterion_id', '')
            desc = getattr(criterion, 'description', '') if not isinstance(criterion, dict) else criterion.get('description', '')
            results.append({
                "criterion_id": cid,
                "description": desc,
                "passed": passed,
                "detail": detail,
            })
        return results

    def verify_evidence_chain(self, task_id: str) -> Dict:
        """Verify the full evidence chain for a task."""
        if not self.evidence:
            return {"task_id": task_id, "passed": False, "error": "No evidence store"}
        return self.evidence.verify_chain(task_id)

    def to_dict(self) -> Dict:
        return {"role": self.role}