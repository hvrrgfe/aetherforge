"""Evidence Store - immutable evidence storage and verification chain.

Evidence is the core integrity mechanism: no claim can be VERIFIED
without evidence from real tool calls captured by the ToolGateway.
"""
import uuid, time, json, threading
from typing import Optional, List, Dict
from aetherforge.agents.protocol import Evidence, EvidenceStatus, Claim

class EvidenceStore:
    """Thread-safe evidence storage with chain verification.

    Evidence is append-only: once stored, it cannot be modified.
    Only status transitions are allowed (PROPOSED -> VERIFIED/REJECTED/INVALIDATED).
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._evidence: Dict[str, Evidence] = {}
        self._claims: Dict[str, Claim] = {}
        self._chains: Dict[str, List[str]] = {}  # task_id -> [evidence_id, ...]

    # --- Evidence CRUD ---

    def store_evidence(self, evidence: Evidence) -> str:
        """Store evidence. Raises ValueError if evidence_id already exists."""
        with self._lock:
            if evidence.evidence_id in self._evidence:
                raise ValueError(f"Evidence {evidence.evidence_id} already exists")
            self._evidence[evidence.evidence_id] = evidence
            if evidence.task_id:
                self._chains.setdefault(evidence.task_id, []).append(evidence.evidence_id)
            return evidence.evidence_id

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        with self._lock:
            return self._evidence.get(evidence_id)

    def get_task_evidence(self, task_id: str) -> List[Evidence]:
        with self._lock:
            return [self._evidence[eid] for eid in self._chains.get(task_id, [])
                    if eid in self._evidence]

    def verify_evidence(self, evidence_id: str, verifier_id: str) -> bool:
        """Mark evidence as verified by a specific verifier."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev or ev.status != EvidenceStatus.PROPOSED:
                return False
            ev.status = EvidenceStatus.VERIFIED
            ev.verified_by = verifier_id
            ev.verified_at = time.time()
            return True

    def reject_evidence(self, evidence_id: str, reason: str = "") -> bool:
        """Mark evidence as rejected."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return False
            ev.status = EvidenceStatus.REJECTED
            ev.metadata["reject_reason"] = reason
            return True

    def invalidate_evidence(self, evidence_id: str, reason: str = "") -> bool:
        """Invalidate evidence (e.g., after rollback)."""
        with self._lock:
            ev = self._evidence.get(evidence_id)
            if not ev:
                return False
            ev.status = EvidenceStatus.INVALIDATED
            ev.metadata["invalidate_reason"] = reason
            return True

    # --- Claims ---

    def store_claim(self, claim: Claim) -> str:
        with self._lock:
            if claim.claim_id in self._claims:
                raise ValueError(f"Claim {claim.claim_id} already exists")
            self._claims[claim.claim_id] = claim
            return claim.claim_id

    def get_claim(self, claim_id: str) -> Optional[Claim]:
        with self._lock:
            return self._claims.get(claim_id)

    def get_task_claims(self, task_id: str) -> List[Claim]:
        with self._lock:
            return [c for c in self._claims.values() if c.task_id == task_id]

    def verify_claim(self, claim_id: str, verifier_id: str) -> bool:
        """Verify a claim by checking all its evidence is VERIFIED."""
        with self._lock:
            claim = self._claims.get(claim_id)
            if not claim or claim.status != EvidenceStatus.PROPOSED:
                return False
            # Check all evidence is verified
            for eid in claim.evidence_ids:
                ev = self._evidence.get(eid)
                if not ev or ev.status != EvidenceStatus.VERIFIED:
                    claim.metadata["blocker"] = f"Evidence {eid} not verified"
                    return False
            claim.status = EvidenceStatus.VERIFIED
            claim.verified_by = verifier_id
            claim.verified_at = time.time()
            return True

    # --- Chain Management ---

    def get_evidence_chain(self, task_id: str) -> List[Dict]:
        """Get full evidence chain for a task as dicts."""
        with self._lock:
            chain = []
            for eid in self._chains.get(task_id, []):
                ev = self._evidence.get(eid)
                if ev:
                    entry = ev.to_dict()
                    # Include linked claim info
                    if ev.claim_id:
                        claim = self._claims.get(ev.claim_id)
                        if claim:
                            entry["claim"] = claim.to_dict()
                    chain.append(entry)
            return chain

    def verify_chain(self, task_id: str) -> Dict:
        """Verify the entire evidence chain for a task.

        Returns a report of passed/failed checks.
        """
        chain = self.get_evidence_chain(task_id)
        result = {"task_id": task_id, "total_evidence": len(chain),
                  "verified": 0, "rejected": 0, "pending": 0,
                  "invalidated": 0, "passed": True, "issues": []}
        for entry in chain:
            status = entry.get("status", "")
            if status == "verified":
                result["verified"] += 1
            elif status == "rejected":
                result["rejected"] += 1
                result["passed"] = False
                result["issues"].append(f"Evidence {entry['evidence_id']} was rejected")
            elif status == "invalidated":
                result["invalidated"] += 1
                result["passed"] = False
                result["issues"].append(f"Evidence {entry['evidence_id']} was invalidated")
            else:
                result["pending"] += 1
                result["passed"] = False
                result["issues"].append(f"Evidence {entry['evidence_id']} is still {status}")
        return result

    # --- Query ---

    def find_evidence(self, source_tool: str = "", status: Optional[EvidenceStatus] = None,
                      task_id: str = "") -> List[Evidence]:
        """Find evidence by filters."""
        with self._lock:
            results = list(self._evidence.values())
            if source_tool:
                results = [e for e in results if e.source_tool == source_tool]
            if status:
                results = [e for e in results if e.status == status]
            if task_id:
                results = [e for e in results if e.task_id == task_id]
            return results

    def count_by_status(self) -> Dict:
        with self._lock:
            counts = {s.value: 0 for s in EvidenceStatus}
            for ev in self._evidence.values():
                counts[ev.status.value] = counts.get(ev.status.value, 0) + 1
            return counts

    def clear_task(self, task_id: str):
        """Remove all evidence and claims for a task (for cleanup)."""
        with self._lock:
            eids = self._chains.pop(task_id, [])
            for eid in eids:
                self._evidence.pop(eid, None)
            cids = [c.claim_id for c in self._claims.values() if c.task_id == task_id]
            for cid in cids:
                self._claims.pop(cid, None)

    def to_dict(self):
        with self._lock:
            return {"evidence_count": len(self._evidence), "claim_count": len(self._claims),
                    "chains": {k: len(v) for k, v in self._chains.items()},
                    "status_counts": self.count_by_status()}