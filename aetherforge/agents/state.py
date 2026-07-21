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

    @world_revision.setter
    def world_revision(self, value):
        with self._lock:
            self._world_revision = value

    @property
    def active_task(self):
        with self._lock:
            task_id = self._active_task_id
            if task_id and task_id in self._tasks:
                return self._tasks[task_id]
            return None

    @active_task.setter
    def active_task(self, task_state):
        with self._lock:
            if task_state:
                self._active_task_id = task_state.task_id
                self._tasks[task_state.task_id] = task_state
            else:
                self._active_task_id = None

    def get_active_task(self):
        with self._lock:
            if self._active_task_id and self._active_task_id in self._tasks:
                return self._tasks[self._active_task_id]
            return None

    def get_task(self, task_id: str):
        with self._lock:
            return self._tasks.get(task_id)

    def next_revision(self):
        with self._lock:
            self._world_revision += 1
            return self._world_revision

    def create_task(self, task_or_id, goal=None):
        with self._lock:
            from aetherforge.agents.protocol import TaskState, TaskPhase
            if isinstance(task_or_id, TaskState):
                task = task_or_id
                task.phase = task.phase or TaskPhase.PLANNING
            else:
                task = TaskState(task_id=task_or_id, goal=goal or "")
                task.phase = TaskPhase.PLANNING
            self._tasks[task.task_id] = task
            self._active_task_id = task.task_id
            return task

    def set_revision(self, rev):
        with self._lock:
            self._world_revision = rev


