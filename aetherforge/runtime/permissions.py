"""Permission Manager - role-based tool access control with default permissions."""
import enum
from typing import Set, Dict, Optional, List


class AgentRole(str, enum.Enum):
    EXPLORER = "explorer"
    PLANNER = "planner"
    BUILDER = "builder"
    VERIFIER = "verifier"
    CRITIC = "critic"
    ORCHESTRATOR = "orchestrator"
    ADMIN = "admin"
    ART_DIRECTOR = "art_director"


class RiskLevel(enum.IntEnum):
    L0_DIRECT = 0
    L1_LIGHT = 1
    L2_STANDARD = 2
    L3_FULL = 3


class ToolPermission(enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    VERIFY = "verify"


_READ_TOOLS = {"observe", "get_", "find_", "list_", "read_", "summar", "diff_"}
_WRITE_TOOLS = _READ_TOOLS | {"create_", "modify_", "set_", "add_", "update_", "delete_", "remove_"}
_ADMIN_TOOLS = _WRITE_TOOLS | {"commit_", "rollback_", "begin_"}
_VERIFY_TOOLS = _READ_TOOLS | {"check_", "verify_", "validate_", "test_", "assert_"}

_RISK_KEYWORDS = {
    RiskLevel.L0_DIRECT: {"query", "list", "get", "observe", "find", "read", "check"},
    RiskLevel.L1_LIGHT: {"set", "update", "add_tag", "rename", "modify"},
    RiskLevel.L2_STANDARD: {"create", "delete", "remove", "spawn", "add_entity",
                            "add_rule", "add_quest", "modify_entity"},
    RiskLevel.L3_FULL: {"commit", "rollback", "batch", "patch", "delete", "replace",
                        "clear", "reset", "import", "export"},
}


def assess_risk_from_goal(goal: str) -> RiskLevel:
    goal_lower = goal.lower()
    for level in [RiskLevel.L3_FULL, RiskLevel.L2_STANDARD, RiskLevel.L1_LIGHT]:
        if any(kw in goal_lower for kw in _RISK_KEYWORDS[level]):
            return level
    return RiskLevel.L0_DIRECT


def get_required_agents(level: RiskLevel) -> List[AgentRole]:
    mapping = {
        RiskLevel.L0_DIRECT: [AgentRole.BUILDER],
        RiskLevel.L1_LIGHT: [AgentRole.PLANNER, AgentRole.BUILDER],
        RiskLevel.L2_STANDARD: [AgentRole.EXPLORER, AgentRole.PLANNER,
                                AgentRole.BUILDER, AgentRole.VERIFIER],
        RiskLevel.L3_FULL: [AgentRole.EXPLORER, AgentRole.PLANNER,
                            AgentRole.BUILDER, AgentRole.VERIFIER, AgentRole.CRITIC],
    }
    return mapping.get(level, [])


class PermissionManager:
    """Manages role-to-tool permissions with default mappings."""

    def __init__(self):
        self._role_perm: Dict[AgentRole, Set[str]] = {
            AgentRole.EXPLORER: _READ_TOOLS.copy(),
            AgentRole.PLANNER: _READ_TOOLS.copy(),
            AgentRole.BUILDER: _WRITE_TOOLS.copy(),
            AgentRole.VERIFIER: _VERIFY_TOOLS.copy(),
            AgentRole.CRITIC: _VERIFY_TOOLS.copy(),
            AgentRole.ORCHESTRATOR: _ADMIN_TOOLS.copy(),
            AgentRole.ADMIN: _ADMIN_TOOLS.copy(),
            AgentRole.ART_DIRECTOR: _READ_TOOLS.copy(),
        }

    def allow(self, role: AgentRole, tool_prefix: str) -> None:
        self._role_perm.setdefault(role, set()).add(tool_prefix)

    def deny(self, role: AgentRole, tool_prefix: str) -> None:
        if role in self._role_perm:
            self._role_perm[role].discard(tool_prefix)

    def can_call(self, role: AgentRole, tool_name: str) -> bool:
        """Check if a role can call a tool. ORCHESTRATOR/ADMIN can call any tool."""
        if role in (AgentRole.ORCHESTRATOR, AgentRole.ADMIN):
            return True
        prefixes = self._role_perm.get(role, set())
        for prefix in prefixes:
            if tool_name.startswith(prefix):
                return True
        return False

    def allowed_tools(self, role: AgentRole) -> Set[str]:
        return self._role_perm.get(role, set()).copy()
