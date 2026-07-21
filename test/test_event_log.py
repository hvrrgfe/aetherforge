"""Tests for runtime/event_log.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from aetherforge.runtime.event_log import EventLog, EventType

def test_event_log_record():
    log = EventLog(max_events=10)
    evt = log.record("test_type", {"key": "value"}, task_id="task_001")
    assert evt["type"] == "test_type"
    assert evt["task_id"] == "task_001"
    assert "event_id" in evt
    print("  [PASS] test_event_log_record")

def test_event_log_query():
    log = EventLog()
    log.record("type_a", {}, task_id="t1")
    log.record("type_b", {}, task_id="t2")
    log.record("type_a", {}, task_id="t1")
    results = log.query(task_id="t1")
    assert len(results) == 2
    results = log.query(event_type="type_a")
    assert len(results) == 2
    print("  [PASS] test_event_log_query")

def test_event_log_convenience():
    log = EventLog()
    e1 = log.record_agent_status("t1", "a1", "builder", "running", "building")
    assert e1["type"] == "agent_status_changed"
    e2 = log.record_world_change(5, [{"type": "entity_created", "id": "e1"}])
    assert e2["type"] == "world_changed"
    e3 = log.record_verification("t1", "failed", 3, 2, 1)
    assert e3["data"]["blocking_findings"] == 1
    print("  [PASS] test_event_log_convenience")

def test_event_log_max_events():
    log = EventLog(max_events=3)
    for i in range(5):
        log.record("evt", {"i": i})
    assert len(log.get_recent(100)) == 3
    print("  [PASS] test_event_log_max_events")

if __name__ == "__main__":
    passed = 0
    failed = 0
    for t in [test_event_log_record, test_event_log_query, test_event_log_convenience, test_event_log_max_events]:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\nResult: {passed}/{passed+failed} passed, {failed} failed")