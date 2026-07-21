"""Agent Protocol Layer - Core types for multi-agent communication.

All types are JSON-serializable for MCP/HTTP transport.
Evidence-based verification ensures agents cannot claim completion without proof.
"""
import uuid, time, json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any

class EvidenceStatus(str, Enum):
    PROPOSED = "proposed"
    VERIFIED = "verified"
    REJECTED = "rejected"
    INVALIDATED = "invalidated"

class TaskPhase(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXPLORING = "exploring"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    REVIEWING = "reviewing"
    REPAIRING = "repairing"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Evidence:
    evidence_id: str = field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    claim_id: str = ""
    source_tool: str = ""
    source_call_id: str = ""
    result: dict = field(default_factory=dict)
    status: Any = EvidenceStatus.PROPOSED
    timestamp: float = field(default_factory=time.time)
    verified_by: str = ""
    verified_at: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "task_id": self.task_id,
            "claim_id": self.claim_id,
            "source_tool": self.source_tool,
            "source_call_id": self.source_call_id,
            "result": self.result,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "timestamp": self.timestamp,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_tool_call(cls, tool_name, call_id, result, task_id="", claim_id=""):
        ev = cls(task_id=task_id, claim_id=claim_id, source_tool=tool_name, source_call_id=call_id)
        if hasattr(result, "to_dict"):
            ev.result = result.to_dict()
        elif isinstance(result, dict):
            ev.result = result
        else:
            ev.result = {"raw": str(result)}
        return ev

@dataclass
class Claim:
    claim_id: str = field(default_factory=lambda: f"cl_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    agent_id: str = ""
    content: str = ""
    category: str = "general"
    evidence_ids: list = field(default_factory=list)
    status: Any = EvidenceStatus.PROPOSED
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    verified_by: str = ""
    verified_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {"claim_id": self.claim_id, "task_id": self.task_id, "agent_id": self.agent_id,
                "content": self.content, "category": self.category, "evidence_ids": self.evidence_ids,
                "status": self.status.value if hasattr(self.status, "value") else str(self.status),
                "created_at": self.created_at, "verified_by": self.verified_by, "verified_at": self.verified_at}

@dataclass
class AcceptanceCriterion:
    criterion_id: str = field(default_factory=lambda: f"ac_{uuid.uuid4().hex[:8]}")
    description: str = ""
    verification_tool: str = ""
    verification_params: dict = field(default_factory=dict)
    expected_result: dict = field(default_factory=dict)
    passed: bool = False
    evidence_id: str = ""

    def to_dict(self) -> dict:
        return {"criterion_id": self.criterion_id, "description": self.description,
                "verification_tool": self.verification_tool, "verification_params": self.verification_params,
                "expected_result": self.expected_result, "passed": self.passed, "evidence_id": self.evidence_id}

@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    sender: str = ""
    recipient: str = ""
    msg_type: str = "fact"
    content: str = ""
    facts: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    evidence_ids: list = field(default_factory=list)
    in_reply_to: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"message_id": self.message_id, "sender": self.sender, "recipient": self.recipient,
                "msg_type": self.msg_type, "content": self.content, "facts": self.facts,
                "assumptions": self.assumptions, "evidence_ids": self.evidence_ids,
                "in_reply_to": self.in_reply_to, "created_at": self.created_at}

@dataclass
class TaskState:
    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    goal: str = ""
    phase: Any = TaskPhase.PENDING
    progress: float = 0.0
    current_step: str = ""
    agents: dict = field(default_factory=dict)
    acceptance_criteria: list = field(default_factory=list)
    passed_checks: int = 0
    failed_checks: int = 0
    total_checks: int = 0
    evidence_ids: list = field(default_factory=list)
    claim_ids: list = field(default_factory=list)
    world_revision: int = 0
    transaction_id: str = ""
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"task_id": self.task_id, "goal": self.goal,
                "phase": self.phase.value if hasattr(self.phase, "value") else str(self.phase),
                "progress": self.progress, "current_step": self.current_step, "agents": self.agents,
                "acceptance_criteria": [c.to_dict() if hasattr(c, "to_dict") else c for c in self.acceptance_criteria],
                "passed_checks": self.passed_checks, "failed_checks": self.failed_checks,
                "total_checks": self.total_checks, "evidence_ids": self.evidence_ids,
                "claim_ids": self.claim_ids, "world_revision": self.world_revision,
                "transaction_id": self.transaction_id, "error": self.error,
                "created_at": self.created_at, "updated_at": self.updated_at}

@dataclass
class AgentTransaction:
    transaction_id: str = field(default_factory=lambda: f"tx_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    world_revision_before: int = 0
    world_revision_after: int = 0
    changes: list = field(default_factory=list)
    evidence_ids: list = field(default_factory=list)
    status: str = "open"
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    committed_at: Optional[float] = None
    rolled_back_at: Optional[float] = None
    committed_by: str = ""

    def to_dict(self) -> dict:
        return {"transaction_id": self.transaction_id, "task_id": self.task_id,
                "world_revision_before": self.world_revision_before,
                "world_revision_after": self.world_revision_after,
                "changes": self.changes, "evidence_ids": self.evidence_ids,
                "status": self.status, "created_at": self.created_at,
                "committed_at": self.committed_at, "rolled_back_at": self.rolled_back_at,
                "committed_by": self.committed_by}

@dataclass
class CompactToolResult:
    success: bool = True
    summary: str = ""
    key_values: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {"success": self.success, "summary": self.summary,
                "key_values": self.key_values, "error": self.error}

    @classmethod
    def from_tool_result(cls, result):
        if hasattr(result, "to_dict"):
            d = result.to_dict()
        elif isinstance(result, dict):
            d = result
        else:
            d = {"success": False, "data": {}, "error": str(result)}
        return cls(success=d.get("success", False), summary=str(d.get("data", {}))[:200],
                   key_values=d.get("data", {}), error=d.get("error"))