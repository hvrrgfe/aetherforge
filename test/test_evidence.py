"""Tests for EvidenceStore."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aetherforge.validation.evidence import EvidenceStore
from aetherforge.agents.protocol import Evidence, EvidenceStatus, Claim

def test_store_and_retrieve():
    store = EvidenceStore()
    ev = Evidence(source_tool="create_entity", source_call_id="call_1",
                  result={"entity_id": "ent_001"}, task_id="task_1")
    eid = store.store_evidence(ev)
    assert eid == ev.evidence_id
    retrieved = store.get_evidence(eid)
    assert retrieved is not None
    assert retrieved.source_tool == "create_entity"
    assert retrieved.status == EvidenceStatus.PROPOSED
    print(f"  [PASS] store_and_retrieve: {eid}")

def test_verify_evidence():
    store = EvidenceStore()
    ev = Evidence(source_tool="get_entity", source_call_id="call_2",
                  result={"exists": True}, task_id="task_1")
    eid = store.store_evidence(ev)
    assert store.verify_evidence(eid, "verifier_01") == True
    ev2 = store.get_evidence(eid)
    assert ev2.status == EvidenceStatus.VERIFIED
    assert ev2.verified_by == "verifier_01"
    assert ev2.verified_at is not None
    print("  [PASS] verify_evidence")

def test_reject_evidence():
    store = EvidenceStore()
    ev = Evidence(source_tool="create_entity", task_id="task_1")
    eid = store.store_evidence(ev)
    assert store.reject_evidence(eid, "Missing required field") == True
    ev2 = store.get_evidence(eid)
    assert ev2.status == EvidenceStatus.REJECTED
    print("  [PASS] reject_evidence")

def test_invalidate_evidence():
    store = EvidenceStore()
    ev = Evidence(source_tool="modify_entity", task_id="task_1")
    eid = store.store_evidence(ev)
    assert store.invalidate_evidence(eid, "Rolled back") == True
    ev2 = store.get_evidence(eid)
    assert ev2.status == EvidenceStatus.INVALIDATED
    print("  [PASS] invalidate_evidence")

def test_claim_with_evidence():
    store = EvidenceStore()
    ev = Evidence(source_tool="get_entity", source_call_id="call_3",
                  result={"exists": True, "name": "Guard"}, task_id="task_1")
    eid = store.store_evidence(ev)
    store.verify_evidence(eid, "verifier_01")

    claim = Claim(task_id="task_1", agent_id="builder_01",
                  content="Guard entity exists", evidence_ids=[eid])
    cid = store.store_claim(claim)
    assert store.verify_claim(cid, "verifier_01") == True
    c2 = store.get_claim(cid)
    assert c2.status == EvidenceStatus.VERIFIED
    print("  [PASS] claim_with_evidence")

def test_reject_claim_missing_evidence():
    store = EvidenceStore()
    claim = Claim(task_id="task_1", agent_id="builder_01",
                  content="Something exists", evidence_ids=["nonexistent"])
    cid = store.store_claim(claim)
    assert store.verify_claim(cid, "verifier_01") == False
    print("  [PASS] reject_claim_missing_evidence")

def test_evidence_chain():
    store = EvidenceStore()
    for i in range(3):
        ev = Evidence(source_tool="tool_a", source_call_id=f"call_{i}",
                      result={"step": i}, task_id="task_chain")
        store.store_evidence(ev)
    chain = store.get_evidence_chain("task_chain")
    assert len(chain) == 3
    report = store.verify_chain("task_chain")
    assert report["total_evidence"] == 3
    assert report["passed"] == False  # all are PROPOSED not verified
    print(f"  [PASS] evidence_chain: {len(chain)} items, passed={report['passed']}")

def test_find_evidence():
    store = EvidenceStore()
    for i in range(5):
        ev = Evidence(source_tool="create_entity" if i % 2 == 0 else "get_entity",
                      task_id=f"task_{i % 2}")
        store.store_evidence(ev)
    found = store.find_evidence(source_tool="create_entity")
    assert len(found) == 3
    found2 = store.find_evidence(task_id="task_0")
    assert len(found2) == 3
    print(f"  [PASS] find_evidence: {len(found)} create, {len(found2)} task_0")

def test_clear_task():
    store = EvidenceStore()
    ev = Evidence(task_id="task_del")
    store.store_evidence(ev)
    assert len(store.get_evidence_chain("task_del")) == 1
    store.clear_task("task_del")
    assert len(store.get_evidence_chain("task_del")) == 0
    print("  [PASS] clear_task")

def test_duplicate_store():
    store = EvidenceStore()
    ev = Evidence()
    eid = store.store_evidence(ev)
    try:
        store.store_evidence(ev)
        assert False, "Should have raised"
    except ValueError:
        pass
    print("  [PASS] duplicate_store raises ValueError")

if __name__ == "__main__":
    tests = [test_store_and_retrieve, test_verify_evidence, test_reject_evidence,
             test_invalidate_evidence, test_claim_with_evidence,
             test_reject_claim_missing_evidence, test_evidence_chain,
             test_find_evidence, test_clear_task, test_duplicate_store]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\nResult: {passed}/{passed+failed} passed, {failed} failed")