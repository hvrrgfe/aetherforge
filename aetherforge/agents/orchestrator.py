"""Agent Orchestrator - coordinates the multi-agent workflow.

Manages task lifecycle, agent role scheduling, and phase transitions.
Integrates risk level routing, approval management, event logging,
and snapshot management.
"""
import uuid, time, threading, json
from typing import Optional, Dict, List, Any, Callable
from aetherforge.agents.protocol import TaskState, TaskPhase, AgentTransaction
from aetherforge.agents.state import AgentStateManager
from aetherforge.agents.errors import TokenBudgetExceeded, PermissionDenied
from aetherforge.agents.policies import AgentPolicy, ApprovalMode, TokenBudget
from aetherforge.agents.gateway import ToolGateway
from aetherforge.agents.model_router import ModelRouter
from aetherforge.agents.context import ContextManager
from aetherforge.agents.approvals import ApprovalManager
from aetherforge.runtime.transaction import TransactionManager
from aetherforge.runtime.event_log import EventLog
from aetherforge.runtime.snapshots import SnapshotManager
from aetherforge.validation.commit_gate import CommitGate, GatePolicy
from aetherforge.validation.evidence import EvidenceStore
from aetherforge.runtime.permissions import AgentRole, RiskLevel, assess_risk_from_goal, get_required_agents

class AgentOrchestrator:
    """Coordinates the multi-agent workflow from task start to commit."""

    def __init__(self, world_model, gateway: ToolGateway,
                 evidence_store: EvidenceStore, commit_gate: CommitGate,
                 state_manager: AgentStateManager = None,
                 model_router: ModelRouter = None,
                 policy: AgentPolicy = None):
        self._world = world_model
        self._gateway = gateway
        self._evidence = evidence_store
        self._gate = commit_gate
        self._state_mgr = state_manager or AgentStateManager()
        self._model = model_router
        self._policy = policy or AgentPolicy()
        self._txm = TransactionManager(world_model, self._state_mgr)
        self._context = ContextManager(world_model)
        self._event_log = EventLog()
        self._snapshots = SnapshotManager()
        self._approvals = ApprovalManager()
        self._lock = threading.Lock()

        # Agent roles (lazy init)
        self._explorer = None
        self._planner = None
        self._builder = None
        self._verifier = None
        self._critic = None
        self._art_director = None

    def _get_explorer(self):
        if not self._explorer:
            from aetherforge.agents.roles import Explorer
            self._explorer = Explorer(self._gateway, self._evidence, self._state_mgr)
        return self._explorer

    def _get_planner(self):
        if not self._planner:
            from aetherforge.agents.roles import Planner
            self._planner = Planner(self._gateway, self._evidence, self._state_mgr)
        return self._planner

    def _get_builder(self):
        if not self._builder:
            from aetherforge.agents.roles import Builder
            self._builder = Builder(self._gateway, self._evidence, self._state_mgr)
        return self._builder

    def _get_verifier(self):
        if not self._verifier:
            from aetherforge.agents.roles import Verifier
            self._verifier = Verifier(self._gateway, self._evidence, self._state_mgr, self._world)
        return self._verifier

    def _get_critic(self):
        if not self._critic:
            from aetherforge.agents.roles import Critic
            self._critic = Critic(self._gateway, self._evidence, self._state_mgr)
        return self._critic

    def _get_art_director(self):
        if not self._art_director:
            from aetherforge.agents.roles import ArtDirector
            self._art_director = ArtDirector(self._gateway, self._evidence, self._state_mgr)
        return self._art_director

    # --- Task Lifecycle ---

    def start_task(self, goal: str, constraints: List[str] = None,
                   approval_mode: str = "") -> Dict:
        """Start a new agent task with risk assessment.
        approval_mode: "always", "high_risk", "never" - defaults from config."""
        if not approval_mode:
            try:
                from aetherforge.config import get_config
                approval_mode = get_config().agent.approval_mode
            except Exception:
                approval_mode = "high_risk"
        """Start a new agent task with risk assessment."""
        task = TaskState(goal=goal)
        task.phase = TaskPhase.PLANNING
        self._state_mgr.create_task(task)

        # Assess risk level
        risk_level = assess_risk_from_goal(goal)
        required_agents = get_required_agents(risk_level)
        task.metadata["risk_level"] = risk_level.value
        task.metadata["required_agents"] = required_agents

        # Start transaction and take snapshot
        tx = self._txm.begin(task_id=task.task_id)
        task.transaction_id = tx.transaction_id
        self._snapshots.take(self._world)

        self._event_log.record("task_started", {
            "goal": goal, "risk_level": risk_level.value,
            "required_agents": required_agents,
        }, task_id=task.task_id)

        return {
            "task_id": task.task_id,
            "transaction_id": tx.transaction_id,
            "status": "planning",
            "goal": goal,
            "risk_level": risk_level.value,
            "required_agents": required_agents,
        }

    def get_status(self, task_id: str) -> Optional[Dict]:
        """Get current task status."""
        task = self._state_mgr.get_task(task_id)
        if not task:
            return None
        return task.to_dict()

    def run_full_cycle(self, task_id: str) -> Dict:
        """Run the agent workflow with risk-appropriate routing.

        Level 0: Builder -> Check
        Level 1: Planner -> Builder -> Check
        Level 2: Explorer -> Planner -> Builder -> Verifier -> Commit
        Level 3: All roles + Human Approval
        """
        task = self._state_mgr.get_task(task_id)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}

        risk_level_str = task.metadata.get("risk_level", "level_2_standard")
        risk_level = RiskLevel(risk_level_str)
        results = {}
        self._snapshots.take(self._world)

        # Phase 1: Explore (Level 2+)
        if risk_level in (RiskLevel.L2_STANDARD, RiskLevel.L3_FULL):
            task.phase = TaskPhase.EXPLORING
            self._gateway.set_role(AgentRole.EXPLORER)
            self._event_log.record_agent_status(task_id, "explorer-001", "explorer", "running", "exploring world")
            explorer = self._get_explorer()
            explore_result = explorer.explore()
            results["explore"] = {"facts": explore_result.get("fact_count", 0)}
            self._state_mgr.update_task(task_id, progress=0.15)

        # Phase 2: Plan (Level 1+)
        if risk_level in (RiskLevel.L1_LIGHT, RiskLevel.L2_STANDARD, RiskLevel.L3_FULL):
            task.phase = TaskPhase.PLANNING
            planner = self._get_planner()
            facts = results.get("explore", {})
            self._event_log.record_agent_status(task_id, "planner-001", "planner", "running", "creating plan")
            plan = planner.create_plan(facts, task.goal)
            results["plan"] = {"steps": plan.get("step_count", 0) if isinstance(plan, dict) else len(plan) if isinstance(plan, (list, tuple)) else 0}
            self._state_mgr.update_task(task_id, progress=0.3)

            # Check if plan approval is needed (Level 3)
            if risk_level == RiskLevel.L3_FULL:
                approval = self._approvals.create_request(
                    task_id, "plan_approval", {"plan": str(plan)[:500]},
                )
                self._event_log.record("approval_requested", {"approval_id": approval.id, "type": "plan"},
                                       task_id=task_id)
                results["plan_approval"] = {"approval_id": approval.id, "status": "awaiting"}

        # Phase 3: Build
        task.phase = TaskPhase.EXECUTING
        self._gateway.set_role(AgentRole.BUILDER)
        self._event_log.record_agent_status(task_id, "builder-001", "builder", "running", "executing plan")
        builder = self._get_builder()
        build_result = builder.execute(plan.get("steps", []) if isinstance(plan, dict) else plan)
        results["build"] = {"changes": build_result.get("change_count", 0)}
        self._state_mgr.update_task(task_id, progress=0.5)

        # Take snapshot after build
        after_build = self._snapshots.take(self._world)
        if after_build:
            diff = self._snapshots.diff_latest(getattr(after_build, 'revision', 0) - 1)
            if diff:
                results["diff"] = diff
                changes_list = []
                for k in ["entities_created", "entities_modified", "entities_removed"]:
                    for eid in diff.get(k, []):
                        changes_list.append({"type": k, "id": eid})
                self._event_log.record_world_change(
                    after_build.revision, changes_list, task_id=task_id
                )

        # Phase 4: Verify (Level 2+)
        if risk_level in (RiskLevel.L2_STANDARD, RiskLevel.L3_FULL):
            task.phase = TaskPhase.VERIFYING
            self._gateway.set_role(AgentRole.VERIFIER)
            self._event_log.record_agent_status(task_id, "verifier-001", "verifier", "running", "verifying world")
            verifier = self._get_verifier()
            verify_result = verifier.verify(task.task_id, task.goal)
            results["verify"] = verify_result
            passed = verify_result.get("passed_count", 0)
            failed = verify_result.get("failed_count", 0)
            self._state_mgr.update_task(task_id, progress=0.7,
                                        passed_checks=passed, failed_checks=failed)
            self._event_log.record_verification(task_id, verify_result.get("status", "unknown"),
                                                 passed, failed, 0)

        # Phase 5: Critic review (Level 3 only)
        critic_findings = []
        if risk_level == RiskLevel.L3_FULL:
            self._gateway.set_role(AgentRole.CRITIC)
            self._event_log.record_agent_status(task_id, "critic-001", "critic", "running", "adversarial review")
            critic = self._get_critic()
            review = critic.review(task_id, self._world)
            results["critic"] = {"issues": review.get("total_issues", 0),
                                 "blocking": review.get("blocking", 0)}
            critic_findings = review.get("issues", [])

            # Art Director review (Level 3 only)
            self._gateway.set_role(AgentRole.ART_DIRECTOR)
            self._event_log.record_agent_status(task_id, "art-001", "art_director", "running", "visual review")
            art = self._get_art_director()
            art_review = art.review_scene(self._world)
            results["art_review"] = art_review

        # Phase 6: Commit Gate
        gate_result = self._gate.can_commit(task_id, task, self._evidence, self._txm,
                                             extra_findings=critic_findings)
        if gate_result.get("allowed"):
            tx = self._txm.commit(committer="orchestrator")
            task.phase = TaskPhase.COMMITTED
            task.world_revision = getattr(tx, 'world_revision_after', 0) if tx else 0
            self._event_log.record_transaction(task_id, task.transaction_id, "committed",
                                                task.world_revision)
            self._event_log.record("task_completed", {"success": True}, task_id=task_id)
        else:
            task.phase = TaskPhase.FAILED
            self._event_log.record("task_completed", {"success": False,
                                   "reason": gate_result.get("reason", "Gate rejected")},
                                   task_id=task_id)

        self._state_mgr.update_task(task_id, progress=1.0)

        return {
            "task_id": task_id,
            "success": gate_result.get("allowed", False),
            "risk_level": risk_level.value,
            "phase": task.phase.value if hasattr(task.phase, 'value') else str(task.phase),
            "results": results,
        }


    def run_with_repair(self, task_id, max_attempts=3):
        """Run agent workflow with automatic repair loop."""
        attempt = 0
        all_results = []
        while attempt < max_attempts:
            attempt += 1
            result = self.run_full_cycle(task_id)
            all_results.append(result)
            if result.get("success"):
                return {"success": True, "attempts": attempt, "results": all_results}
            task = self._state_mgr.get_task(task_id)
            if not task or task.phase.value == "rolled_back":
                break
            self._gateway.set_role(AgentRole.CRITIC)
            critic = self._get_critic()
            review = critic.review(task_id, self._world)
            if not review.get("repairable"):
                return {"success": False, "attempts": attempt,
                        "reason": "Not repairable", "results": all_results}
            repair_plan = critic.generate_repair_plan(review.get("issues", []))
            if not repair_plan:
                return {"success": False, "attempts": attempt,
                        "reason": "No repair steps", "results": all_results}
            self._gateway.set_role(AgentRole.BUILDER)
            self._event_log.record_agent_status(task_id, "builder-001", "builder",
                                                 "repairing", f"attempt {attempt}")
            for rp in repair_plan:
                tool = rp.get("tool", "")
                params = rp.get("params", {})
                try:
                    self._gateway.call_tool(tool, **params)
                except Exception:
                    pass
            task.phase = TaskPhase.REPAIRING
            self._state_mgr.update_task(task_id, phase=TaskPhase.REPAIRING)
        return {"success": False, "attempts": attempt,
                "reason": f"Max attempts ({max_attempts})", "results": all_results}

    def commit_task(self, task_id: str, committer: str = "user") -> Dict:
        """Commit the active transaction for a task."""
        result = self._gate.can_commit(task_id, self._state_mgr.get_task(task_id),
                                        self._evidence, self._txm)
        if not result.get("allowed"):
            return {"success": False, "error": "Commit gate rejected",
                    "blocking": result.get("blocking", [])}
        tx = self._txm.commit(committer=committer)
        task = self._state_mgr.get_task(task_id)
        if task:
            task.phase = TaskPhase.COMMITTED
            task.world_revision = getattr(tx, 'world_revision_after', 0) if tx else 0
        self._event_log.record_transaction(task_id, task.transaction_id if task else "",
                                            "committed", task.world_revision if task else 0)
        return {"success": True, "transaction_id": getattr(tx, 'transaction_id', ''),
                "world_revision": getattr(tx, 'world_revision_after', 0)}

    def rollback_task(self, task_id: str) -> Dict:
        """Rollback the active transaction for a task."""
        task = self._state_mgr.get_task(task_id)
        if not task:
            return {"success": True, "note": "Task not found, nothing to rollback"}
        tx = self._txm.rollback()
        task.phase = TaskPhase.ROLLED_BACK
        self._event_log.record_transaction(task_id, getattr(tx, 'transaction_id', ''),
                                            "rolled_back", 0)
        return {"success": True, "transaction_id": getattr(tx, 'transaction_id', '')}

    def request_approval(self, task_id: str, message: str = "") -> Dict:
        """Request human approval for a blocked task."""
        task = self._state_mgr.get_task(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        req = self._approvals.create_request(task_id, "commit_approval",
                                             {"message": message})
        self._event_log.record("approval_requested",
                               {"approval_id": req.id, "type": "commit"},
                               task_id=task_id)
        return {
            "task_id": task_id,
            "approval_id": req.id,
            "status": "awaiting_approval",
            "phase": task.phase.value if hasattr(task.phase, 'value') else str(task.phase),
            "message": message,
        }

    def resolve_approval(self, approval_id: str, approved: bool,
                         approver: str = "user") -> Dict:
        """Resolve an approval request."""
        result = self._approvals.resolve(approval_id, approved, approver)
        self._event_log.record("approval_resolved",
                               {"approval_id": approval_id, "approved": approved},
                               task_id=result.get("task_id", ""))
        return result

    def get_pending_approvals(self, task_id: str = "") -> List[Dict]:
        """Get pending approval requests."""
        return self._approvals.get_pending(task_id)

    def get_evidence(self, task_id: str) -> List[Dict]:
        """Get evidence chain for a task."""
        return self._evidence.get_evidence_chain(task_id) if self._evidence else []

    def get_report(self, task_id: str) -> Dict:
        """Get a comprehensive report for a task."""
        task = self._state_mgr.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        evidence_chain = self.get_evidence(task_id)
        tx_log = self._txm.get_task_transactions(task_id)
        events = self._event_log.query(task_id=task_id, limit=20)
        return {
            "task_id": task_id,
            "goal": task.goal,
            "phase": task.phase.value if hasattr(task.phase, 'value') else str(task.phase),
            "progress": task.progress,
            "risk_level": task.metadata.get("risk_level", "unknown"),
            "checks": {"passed": task.passed_checks, "failed": task.failed_checks,
                       "total": task.total_checks},
            "evidence": len(evidence_chain),
            "transactions": [t.to_dict() for t in tx_log],
            "events": events,
            "world_revision": task.world_revision,
        }

    def get_event_log(self, task_id: str = "", limit: int = 50) -> List[Dict]:
        """Get event log entries."""
        return self._event_log.query(task_id=task_id, limit=limit)

    def to_dict(self) -> Dict:
        return {
            "active_task": self._state_mgr.active_task_id,
            "gate_policy": self._gate.policy.value if hasattr(self._gate.policy, 'value') else str(self._gate.policy),
            "has_active_tx": self._txm.has_active_transaction,
            "event_count": len(self._event_log.get_recent(0)),
        }
