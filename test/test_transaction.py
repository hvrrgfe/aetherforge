"""Tests for Transaction Manager and Commit Gate."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aetherforge.runtime.transaction import TransactionManager
from aetherforge.validation.commit_gate import CommitGate, GatePolicy, CheckResult, CheckSeverity
from aetherforge.agents.protocol import TaskState, TaskPhase, Evidence
from aetherforge.agents.state import AgentStateManager
from aetherforge.validation.evidence import EvidenceStore

class MockWorld:
    def __init__(self):
        self.entities = {}
        self.rules = {}
        self.quests = {}
        self.behaviors = {}
        self.player_entity_id = None
        self.weather = "clear"
        self._history = []

    def _checkpoint(self):
        import copy
        self._history.append({"entities": copy.deepcopy(self.entities)})

    def create_entity(self, eid, data):
        self._checkpoint()
        self.entities[eid] = data
        return eid

def test_begin_transaction():
    world = MockWorld()
    sm = AgentStateManager()
    txm = TransactionManager(world, sm)
    tx = txm.begin(task_id="task_1")
    assert tx.status == "open"
    assert txm.has_active_transaction
    txm.rollback()
    print("  [PASS] begin_transaction")

def test_commit_transaction():
    world = MockWorld()
    sm = AgentStateManager()
    txm = TransactionManager(world, sm)
    txm.begin(task_id="task_1")
    world.create_entity("ent_1", {"name": "Guard"})
    txm.record_change("create", "ent_1")
    committed = txm.commit(committer="verifier_01")
    assert committed.status == "committed"
    assert committed.committed_by == "verifier_01"
    assert not txm.has_active_transaction
    print("  [PASS] commit_transaction")

def test_rollback_transaction():
    world = MockWorld()
    sm = AgentStateManager()
    txm = TransactionManager(world, sm)
    world.create_entity("ent_0", {"name": "Original"})
    txm.begin(task_id="task_2")
    world.create_entity("ent_1", {"name": "ToRemove"})
    rolled = txm.rollback()
    assert rolled.status == "rolled_back"
    assert not txm.has_active_transaction
    print("  [PASS] rollback_transaction")

def test_no_double_begin():
    world = MockWorld()
    sm = AgentStateManager()
    txm = TransactionManager(world, sm)
    txm.begin()
    try:
        txm.begin()
        assert False
    except RuntimeError:
        pass
    txm.rollback()
    print("  [PASS] no_double_begin")

def test_get_transactions():
    world = MockWorld()
    sm = AgentStateManager()
    txm = TransactionManager(world, sm)
    txm.begin(task_id="task_a")
    txm.commit()
    txm.begin(task_id="task_b")
    txm.commit()
    assert len(txm.get_task_transactions("task_a")) == 1
    print("  [PASS] get_transactions")

def test_gate_allows_commit():
    gate = CommitGate(GatePolicy.NORMAL)
    task = TaskState(goal="test")
    task.phase = TaskPhase.VERIFYING
    es = EvidenceStore()
    ev = Evidence(source_tool="get_entity", task_id=task.task_id, result={"exists": True})
    eid = es.store_evidence(ev)
    es.verify_evidence(eid, "verifier")
    world = MockWorld()
    sm = AgentStateManager()
    txm = TransactionManager(world, sm)
    txm.begin(task_id=task.task_id)
    result = gate.can_commit(task.task_id, task, es, txm)
    txm.rollback()
    assert result["allowed"]
    print("  [PASS] gate_allows_commit")

def test_gate_blocks_bad_phase():
    gate = CommitGate(GatePolicy.NORMAL)
    task = TaskState(goal="test")
    task.phase = TaskPhase.PLANNING
    result = gate.can_commit(task.task_id, task)
    assert not result["allowed"]
    print("  [PASS] gate_blocks_bad_phase")

def test_register_custom_check():
    gate = CommitGate(GatePolicy.STRICT)
    gate.register_check(lambda tid: CheckResult("custom", CheckSeverity.PASS))
    task = TaskState(goal="test")
    task.phase = TaskPhase.VERIFYING
    result = gate.can_commit(task.task_id, task)
    print(f"  [PASS] register_custom_check: allowed={result['allowed']}")

if __name__ == "__main__":
    tests = [test_begin_transaction, test_commit_transaction, test_rollback_transaction,
             test_no_double_begin, test_get_transactions, test_gate_allows_commit,
             test_gate_blocks_bad_phase, test_register_custom_check]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            import traceback
            print(f"  [FAIL] {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\nResult: {passed}/{passed+failed} passed, {failed} failed")