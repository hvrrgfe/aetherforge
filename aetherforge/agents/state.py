"""Agent State Management - tracks world revision and agent state."""
import json, threading, time
from typing import Optional
from pathlib import Path
from aetherforge.agents.protocol import TaskState, TaskPhase

class AgentStateManager:
    """Manages Agent runtime state, world revision, and task tracking."""

    def __init__(self, state_dir=None):
        self._lock = threading.Lock()
        self._world_revision = 0
        self._tasks = {}
        self._active_task_id = None
        self._state_dir = Path(state_dir) if state_dir else None
        if self._state_dir:
            self._state_dir.mkdir(parents=True, exist_ok=True)

    @property
    def world_revision(self):
        with self._lock:
            return self._world_revision

    def next_revision(self):
        with self._lock:
            self._world_revision += 1
            return self._world_revision

    def set_revision(self, rev):
        with self._lock:
            self._world_revision = rev

    def create_task(self, task):
        with self._lock:
            self._tasks[task.task_id] = task
            if self._active_task_id is None:
                self._active_task_id = task.task_id
            return task.task_id

    def get_task(self, task_id):
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id, **kwargs):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            for key, val in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, val)
            task.updated_at = time.time()
            return True

    def set_task_phase(self, task_id, phase):
        return self.update_task(task_id, phase=phase)

    def set_active_task(self, task_id):
        with self._lock:
            if task_id in self._tasks:
                self._active_task_id = task_id
                return True
            return False

    @property
    def active_task(self):
        with self._lock:
            if self._active_task_id:
                return self._tasks.get(self._active_task_id)
            return None

    def list_tasks(self, status_filter=None):
        with self._lock:
            tasks = list(self._tasks.values())
            if status_filter:
                tasks = [t for t in tasks if (hasattr(t.phase, "value") and t.phase.value == status_filter) or str(t.phase) == status_filter]
            return [t.to_dict() for t in tasks]

    def remove_task(self, task_id):
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                if self._active_task_id == task_id:
                    self._active_task_id = None
                return True
            return False

    def save_to_file(self, path=None):
        target = Path(path) if path else (self._state_dir / "agent_state.json") if self._state_dir else None
        if not target:
            raise ValueError("No state path configured")
        with self._lock:
            state = {"world_revision": self._world_revision, "active_task_id": self._active_task_id,
                     "tasks": {tid: t.to_dict() for tid, t in self._tasks.items()}}
        target.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(target)

    def load_from_file(self, path=None):
        target = Path(path) if path else (self._state_dir / "agent_state.json") if self._state_dir else None
        if not target or not target.exists():
            return False
        state = json.loads(target.read_text(encoding="utf-8"))
        with self._lock:
            self._world_revision = state.get("world_revision", 0)
            self._active_task_id = state.get("active_task_id")
            self._tasks = {}
            for tid, tdata in state.get("tasks", {}).items():
                phase_val = tdata.pop("phase", "pending")
                tdata.pop("acceptance_criteria", None)
                task = TaskState(**tdata)
                for p in TaskPhase:
                    if p.value == phase_val:
                        task.phase = p
                        break
                self._tasks[tid] = task
        return True

    def to_dict(self):
        with self._lock:
            return {"world_revision": self._world_revision,
                    "active_task_id": self._active_task_id, "task_count": len(self._tasks)}