"""Commit Gate - controls whether a transaction can be committed.

Implements configurable policies:
- strict: All checks must pass, no exceptions
- normal: All checks must pass, minor warnings allowed
- permissive: Only blocking checks enforced
"""
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from aetherforge.agents.protocol import TaskState, TaskPhase
from aetherforge.agents.errors import CommitGateError

class GatePolicy(str, Enum):
    STRICT = "strict"
    NORMAL = "normal"
    PERMISSIVE = "permissive"

class CheckSeverity(str, Enum):
    """Severity of a check result."""
    PASS = "pass"
    WARNING = "warning"
    BLOCKING = "blocking"

class CheckResult:
    """Result of a single commit gate check."""
    def __init__(self, name: str, severity: CheckSeverity, message: str = ""):
        self.name = name
        self.severity = severity
        self.message = message

    def to_dict(self) -> dict:
        return {"name": self.name, "severity": self.severity.value, "message": self.message}

class CommitGate:
    """Gate that decides whether a transaction may be committed.

    Collects checks from multiple sources and applies the configured policy.
    """

    def __init__(self, policy: GatePolicy = GatePolicy.NORMAL):
        self._policy = policy
        self._checks: List[Callable[[str], CheckResult]] = []
        self._history: List[dict] = []

    @property
    def policy(self) -> GatePolicy:
        return self._policy

    def set_policy(self, policy: GatePolicy) -> None:
        self._policy = policy

    def register_check(self, check_fn: Callable[[str], CheckResult]) -> None:
        """Register a check function. Takes task_id, returns CheckResult."""
        self._checks.append(check_fn)

    def can_commit(self, task_id: str, task_state: Optional[TaskState] = None,
                   evidence_store=None, tx_manager=None,
                   extra_findings: List[Dict] = None) -> Dict:
        """Evaluate all registered checks and determine if commit is allowed.

        Args:
            task_id: The task to check.
            task_state: Current task state.
            evidence_store: Evidence store for verification.
            tx_manager: Transaction manager.
            extra_findings: Additional findings from Critic/ArtDirector review.

        Returns a dict with:
        - allowed: bool
        - results: list of CheckResult dicts
        - blocking: list of blocking issue messages
        """
        results = []

        # Built-in checks
        results.append(self._check_phase(task_state))
        results.append(self._check_evidence(task_id, evidence_store))
        results.append(self._check_transaction(task_id, tx_manager))

        # Critic/ArtDirector extra findings check
        if extra_findings:
            blocking_findings = [f for f in extra_findings if f.get("blocking") or f.get("severity") in ("critical", "high")]
            if blocking_findings:
                descs = [f.get("description", f.get("type", "unknown")) for f in blocking_findings[:5]]
                results.append(CheckResult("critic_review", CheckSeverity.BLOCKING,
                                           f"Blocking findings: {', '.join(descs)}"))
            else:
                results.append(CheckResult("critic_review", CheckSeverity.PASS,
                                           f"{len(extra_findings)} non-blocking findings"))

        # Custom registered checks
        for check_fn in self._checks:
            try:
                result = check_fn(task_id)
                if isinstance(result, CheckResult):
                    results.append(result)
            except Exception as e:
                results.append(CheckResult(f"custom_check_{len(results)}",
                    CheckSeverity.BLOCKING, str(e)))

        # Apply policy
        allowed = True
        blocking = []
        warnings = []
        for r in results:
            if r.severity == CheckSeverity.BLOCKING:
                allowed = False
                blocking.append(f"[BLOCKING] {r.name}: {r.message}")
            elif r.severity == CheckSeverity.WARNING:
                warnings.append(f"[WARNING] {r.name}: {r.message}")
                if self._policy == GatePolicy.STRICT:
                    allowed = False

        # Record to history
        decision = {
            "task_id": task_id,
            "policy": self._policy.value,
            "allowed": allowed,
            "results": [r.to_dict() for r in results],
            "blocking": blocking,
            "warnings": warnings,
            "timestamp": __import__("time").time(),
        }
        self._history.append(decision)

        return decision

    def _check_phase(self, task_state: Optional[TaskState]) -> CheckResult:
        """Check that the task is in a committable phase."""
        if task_state is None:
            return CheckResult("phase_check", CheckSeverity.BLOCKING,
                               "No task state provided")
        committable = [TaskPhase.VERIFYING, TaskPhase.REVIEWING, TaskPhase.COMMITTED]
        if task_state.phase in committable or task_state.phase.value in [p.value for p in committable]:
            return CheckResult("phase_check", CheckSeverity.PASS,
                               f"Task in phase: {task_state.phase.value if hasattr(task_state.phase, 'value') else task_state.phase}")
        return CheckResult("phase_check", CheckSeverity.BLOCKING,
                           f"Task in phase: {task_state.phase.value if hasattr(task_state.phase, 'value') else task_state.phase}")

    def _check_evidence(self, task_id: str, evidence_store) -> CheckResult:
        """Check that evidence chain is complete and verified."""
        if evidence_store is None:
            return CheckResult("evidence_check", CheckSeverity.WARNING,
                               "No evidence store configured")
        chain = evidence_store.get_evidence_chain(task_id)
        if not chain:
            return CheckResult("evidence_check", CheckSeverity.BLOCKING,
                               "No evidence found for task")
        report = evidence_store.verify_chain(task_id)
        if report["passed"]:
            return CheckResult("evidence_check", CheckSeverity.PASS,
                               f"{report['verified']}/{report['total_evidence']} evidence verified")
        return CheckResult("evidence_check", CheckSeverity.BLOCKING,
                           f"Evidence issues: {report['issues'][:3]}")

    def _check_transaction(self, task_id: str, tx_manager) -> CheckResult:
        """Check that a valid transaction exists."""
        if tx_manager is None:
            return CheckResult("transaction_check", CheckSeverity.WARNING,
                               "No transaction manager configured")
        if tx_manager.has_active_transaction:
            return CheckResult("transaction_check", CheckSeverity.PASS,
                               f"Active tx: {tx_manager.active_transaction_id}")
        return CheckResult("transaction_check", CheckSeverity.BLOCKING,
                           "No active transaction")

    def get_history(self, limit: int = 10) -> List[dict]:
        return self._history[-limit:]

    def to_dict(self) -> dict:
        return {
            "policy": self._policy.value,
            "check_count": len(self._checks),
            "history_count": len(self._history),
        }