"""Approval Manager - handles human-in-the-loop approval requests.

Tracks approval requests for plans, high-risk operations,
commits, and rollbacks. Supports timeout-based auto-rejection.
"""
import uuid, time, threading, json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

class ApprovalType(str, Enum):
    PLAN_APPROVAL = "plan_approval"
    HIGH_RISK_OPERATION = "high_risk_operation"
    COMMIT_APPROVAL = "commit_approval"
    ROLLBACK_APPROVAL = "rollback_approval"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ApprovalRequest:
    """A single approval request with metadata."""

    def __init__(self, task_id: str, approval_type: str,
                 details: Dict, timeout_seconds: int = 300):
        self.id = f"apr_{uuid.uuid4().hex[:12]}"
        self.task_id = task_id
        self.type = approval_type
        self.details = details
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=timeout_seconds)
        self.resolved_at = None
        self.approver = ""

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "type": self.type,
            "status": self.status.value,
            "details": self.details,
            "created_at": self.created_at.isoformat() + "Z",
            "expires_at": self.expires_at.isoformat() + "Z",
            "resolved_at": self.resolved_at.isoformat() + "Z" if self.resolved_at else None,
            "approver": self.approver,
        }

class ApprovalManager:
    """Manages approval requests with timeout and tracking."""

    def __init__(self, persist_path: str = ""):
        self._requests: Dict[str, ApprovalRequest] = {}
        self._lock = threading.Lock()
        self._persist_path = persist_path or str(Path.home() / ".aetherforge" / "approvals.json")
        self._load()

    def _persist_path_check(self):
        p = Path(self._persist_path)
        p.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        try:
            p = Path(self._persist_path)
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                self._requests = {}
                for req_id, req_data in data.items():
                    r = ApprovalRequest(req_data["task_id"], req_data["type"], req_data.get("details", {}))
                    r.id = req_id
                    r.status = ApprovalStatus(req_data.get("status", "pending"))
                    r.created_at = datetime.fromisoformat(req_data["created_at"].replace("Z", ""))
                    if req_data.get("resolved_at"):
                        r.resolved_at = datetime.fromisoformat(req_data["resolved_at"].replace("Z", ""))
                    r.approver = req_data.get("approver", "")
                    self._requests[req_id] = r
        except Exception:
            self._requests = {}

    def _save(self):
        try:
            self._persist_path_check()
            data = {}
            for req_id, r in self._requests.items():
                data[req_id] = r.to_dict()
            Path(self._persist_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def create_request(self, task_id: str, approval_type: str,
                       details: Dict, timeout_seconds: int = 300) -> ApprovalRequest:
        """Create a new approval request."""
        req = ApprovalRequest(task_id, approval_type, details, timeout_seconds)
        with self._lock:
            self._requests[req.id] = req
        self._save()
        return req

    def resolve(self, approval_id: str, approved: bool,
                approver: str = "user") -> Dict:
        """Resolve a pending approval request."""
        with self._lock:
            req = self._requests.get(approval_id)
            if not req:
                return {"success": False, "error": f"Approval {approval_id} not found"}
            if req.status != ApprovalStatus.PENDING:
                return {"success": False, "error": f"Approval already {req.status.value}"}
            req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            req.resolved_at = datetime.utcnow()
            req.approver = approver
        self._save()
        return {"success": True, "approval_id": approval_id,
                "status": req.status.value, "task_id": req.task_id}

    def get_pending(self, task_id: str = "") -> List[Dict]:
        """Get all pending approvals, optionally filtered by task."""
        self._auto_expire()
        results = []
        with self._lock:
            for req in self._requests.values():
                if req.status != ApprovalStatus.PENDING:
                    continue
                if task_id and req.task_id != task_id:
                    continue
                results.append(req.to_dict())
        return results

    def get_task_approvals(self, task_id: str) -> List[Dict]:
        """Get all approvals for a task."""
        self._auto_expire()
        results = []
        with self._lock:
            for req in self._requests.values():
                if req.task_id == task_id:
                    results.append(req.to_dict())
        return results

    def _auto_expire(self):
        """Auto-expire timed-out requests."""
        now = datetime.utcnow()
        with self._lock:
            for req in self._requests.values():
                if req.status == ApprovalStatus.PENDING and now > req.expires_at:
                    req.status = ApprovalStatus.EXPIRED

    def to_dict(self) -> Dict:
        self._auto_expire()
        pending = sum(1 for r in self._requests.values() if r.status == ApprovalStatus.PENDING)
        return {"total": len(self._requests), "pending": pending}
