"""Transaction Manager - world state transaction support with checkpoint/rollback."""
import uuid, time, copy, threading
from typing import Optional, List, Dict, Any


class Transaction:
    """A single transaction with checkpoint support."""

    def __init__(self, transaction_id: str, task_id: str = ""):
        self.transaction_id = transaction_id
        self.task_id = task_id
        self.status = "open"
        self.changes = []
        self.checkpoint = None
        self.committed_by = ""
        self.committed_at = 0.0


class TransactionManager:
    """Manages world transactions with checkpoint-based rollback."""

    def __init__(self, world_model, state_manager=None):
        self._world = world_model
        self._state_mgr = state_manager
        self._current: Optional[Transaction] = None
        self._history: List[Transaction] = []
        self._lock = threading.Lock()

    @property
    def active_transaction_id(self):
        return self._current.transaction_id if self._current else None

    @property

    def has_active_transaction(self) -> bool:
        return self._current is not None and self._current.status == "open"

    def begin(self, task_id: str = "") -> Transaction:
        with self._lock:
            if self.has_active_transaction:
                raise RuntimeError("A transaction is already open")
            tx = Transaction(transaction_id=f"tx_{uuid.uuid4().hex[:8]}", task_id=task_id)
            # Save checkpoint
            tx.checkpoint = copy.deepcopy(getattr(self._world, "entities", {}))
            self._current = tx
            return tx

    def commit(self, committer: str = "") -> Transaction:
        with self._lock:
            if not self._current or self._current.status != "open":
                raise RuntimeError("No active transaction to commit")
            self._current.status = "committed"
            self._current.committed_by = committer
            self._current.committed_at = time.time()
            self._history.append(self._current)
            if self._state_mgr:
                self._state_mgr.world_revision += 1
            tx = self._current
            self._current = None
            return tx

    def rollback(self) -> Transaction:
        with self._lock:
            if not self._current or self._current.status != "open":
                raise RuntimeError("No active transaction to rollback")
            # Restore checkpoint
            if self._current.checkpoint is not None:
                if hasattr(self._world, "entities"):
                    self._world.entities = copy.deepcopy(self._current.checkpoint)
            self._current.status = "rolled_back"
            self._history.append(self._current)
            tx = self._current
            self._current = None
            return tx

    def record_change(self, operation: str, entity_id: str, data: Dict = None) -> None:
        if self._current:
            self._current.changes.append({
                "op": operation, "entity_id": entity_id, "data": data or {},
            })

    def get_task_transactions(self, task_id: str) -> List[Transaction]:
        return [tx for tx in self._history if tx.task_id == task_id]
