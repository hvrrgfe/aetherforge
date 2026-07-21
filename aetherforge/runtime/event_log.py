"""Event Log - structured runtime event recording with convenience methods."""
import time, threading
from typing import Optional, List, Dict, Any


class EventType:
    AGENT_STATUS_CHANGED = "agent_status_changed"
    WORLD_CHANGED = "world_changed"
    TOOL_CALLED = "tool_called"
    VERIFICATION_UPDATED = "verification_updated"
    TRANSACTION_STATUS_CHANGED = "transaction_status_changed"


class EventLog:
    """Thread-safe event log with query support."""

    def __init__(self, max_events: int = 10000):
        self._lock = threading.Lock()
        self._events: List[Dict] = []
        self._max_events = max_events

    def record(self, event_type: str, data: Dict, task_id: str = "") -> Dict:
        event = {
            "event_id": f"evt_{int(time.time()*1000000)}_{len(self._events)}",
            "type": event_type,
            "task_id": task_id,
            "data": data,
            "timestamp": time.time(),
        }
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]
        return event

    def query(self, event_type: Optional[str] = None, task_id: str = "",
              limit: int = 100) -> List[Dict]:
        results = []
        with self._lock:
            for e in reversed(self._events):
                if event_type and e["type"] != event_type:
                    continue
                if task_id and e["task_id"] != task_id:
                    continue
                results.append(e)
                if len(results) >= limit:
                    break
        return results

    def get_recent(self, count: int = 10) -> List[Dict]:
        with self._lock:
            return list(reversed(self._events[-count:]))

    # Convenience methods
    def record_agent_status(self, task_id: str, agent_id: str, role: str,
                            status: str, action: str) -> Dict:
        return self.record(EventType.AGENT_STATUS_CHANGED, {
            "agent_id": agent_id, "role": role, "status": status, "action": action,
        }, task_id=task_id)

    def record_world_change(self, revision: int, changes: List) -> Dict:
        return self.record(EventType.WORLD_CHANGED, {
            "revision": revision, "changes": changes,
        })

    def record_transaction(self, task_id, transaction_id, status, revision):
        return self.record(EventType.TRANSACTION_STATUS_CHANGED, {
            "transaction_id": transaction_id, "status": status, "revision": revision,
        }, task_id=task_id)

    def record_verification(self, task_id: str, status: str, passed: int,
                            failed: int, blocking: int) -> Dict:
        return self.record(EventType.VERIFICATION_UPDATED, {
            "passed_checks": passed, "failed_checks": failed,
            "blocking_findings": blocking,
        }, task_id=task_id)
