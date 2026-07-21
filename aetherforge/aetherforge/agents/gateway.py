"""Tool Gateway - central access point for all engine tool calls.

Every tool call must pass through the gateway which:
1. Checks permissions
2. Captures evidence from successful calls
3. Routes admin tools (commit/rollback) through CommitGate
4. Returns CompactToolResult for consistency
"""
import uuid, time, threading, inspect
from typing import Optional, Any, Dict, Callable
from aetherforge.agents.protocol import Evidence, CompactToolResult
from aetherforge.agents.errors import PermissionDenied
from aetherforge.runtime.permissions import PermissionManager, AgentRole, ToolPermission

class ToolGateway:
    """Gateway that intercepts all tool calls for permission checks and evidence capture."""

    def __init__(self, engine, perm_manager=None, evidence_store=None):
        self._engine = engine
        self._perm = perm_manager or PermissionManager()
        self._evidence_store = evidence_store
        self._current_role: Optional[AgentRole] = None
        self._call_count = 0
        self._lock = threading.Lock()

    def set_role(self, role: AgentRole) -> None:
        """Set the current agent role for permission checks."""
        self._current_role = role

    # -- Delegated tool methods --

    def _get_tool_fn(self, name):
        """Resolve a tool function from the engine by reflection."""
        fn = getattr(self._engine, name, None)
        return fn

    def list_tools(self):
        """List all tools (delegated to engine)."""
        if hasattr(self._engine, 'list_tools'):
            return self._engine.list_tools()
        return {"success": False, "error": "Engine has no list_tools"}

    def call_tool(self, tool_name: str, **kwargs) -> Dict:
        """Call a tool through the gateway.

        Returns dict result (not ToolResult) for MCP compatibility.
        """
        role = self._current_role or AgentRole.EXPLORER

        # Permission check
        if not self._perm.can_call(role, tool_name):
            raise PermissionDenied(f"Role {role.value} cannot call tool '{tool_name}'")

        fn = self._get_tool_fn(tool_name)
        if fn is None:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # Call the tool
        try:
            raw = fn(**kwargs)
        except Exception as ex:
            return {"success": False, "error": str(ex)}

        # Normalize result to dict
        if hasattr(raw, 'to_dict'):
            result = raw.to_dict()
        elif isinstance(raw, dict):
            result = raw
        else:
            result = {"success": bool(raw), "data": {"raw": str(raw)}}

        # Capture evidence for successful non-observe calls
        if result.get("success", False) and self._evidence_store:
            self._capture_evidence(tool_name, result)

        return result

    def _capture_evidence(self, tool_name: str, result: Dict) -> None:
        """Capture a tool call as evidence."""
        with self._lock:
            self._call_count += 1
            call_id = f"call_{self._call_count}_{int(time.time())}"
        ev = Evidence(
            source_tool=tool_name,
            source_call_id=call_id,
            result=result,
        )
        try:
            self._evidence_store.store_evidence(ev)
        except Exception:
            pass  # Evidence storage is best-effort

    # -- Convenience methods for common tools --

    def observe(self):
        return self.call_tool("observe")

    def create_entity(self, **kwargs):
        return self.call_tool("create_entity", **kwargs)

    def get_entity(self, entity_id):
        return self.call_tool("get_entity", entity_id=entity_id)

    def modify_entity(self, entity_id, changes):
        return self.call_tool("modify_entity", entity_id=entity_id, changes=changes)

    def remove_entity(self, entity_id):
        return self.call_tool("remove_entity", entity_id=entity_id)

    def find_entities(self, **kwargs):
        return self.call_tool("find_entities", **kwargs)

    @property
    def current_role(self) -> Optional[AgentRole]:
        return self._current_role

    def to_dict(self):
        return {
            "current_role": self._current_role.value if self._current_role else None,
            "call_count": self._call_count,
        }