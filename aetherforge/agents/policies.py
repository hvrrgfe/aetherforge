"""Agent Policies - configuration for agent behavior, retries, and token budgets."""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class ApprovalMode(str, Enum):
    AUTO = "auto"
    HIGH_RISK = "high_risk"
    MANUAL = "manual"

@dataclass
class TokenBudget:
    """Token budget tracking for a task."""
    max_tokens: int = 4000
    used_tokens: int = 0
    warn_at: float = 0.8
    hard_limit: bool = True

    @property
    def remaining(self) -> int:
        return max(0, self.max_tokens - self.used_tokens)

    @property
    def exhausted(self) -> bool:
        return self.hard_limit and self.used_tokens >= self.max_tokens

    @property
    def warning(self) -> bool:
        return self.used_tokens >= self.max_tokens * self.warn_at

    def use(self, tokens: int) -> bool:
        if self.exhausted:
            return False
        self.used_tokens += tokens
        return True

    def to_dict(self) -> dict:
        return {"max_tokens": self.max_tokens, "used_tokens": self.used_tokens,
                "remaining": self.remaining, "exhausted": self.exhausted,
                "warning": self.warning}

@dataclass
class AgentPolicy:
    """Configuration for an agent's behavior."""
    max_retries: int = 3
    timeout_seconds: float = 60.0
    approval_mode: ApprovalMode = ApprovalMode.HIGH_RISK
    token_budget: TokenBudget = field(default_factory=TokenBudget)
    require_evidence: bool = True
    auto_repair: bool = True
    max_repair_attempts: int = 3

    def to_dict(self) -> dict:
        return {"max_retries": self.max_retries, "timeout_seconds": self.timeout_seconds,
                "approval_mode": self.approval_mode.value, "token_budget": self.token_budget.to_dict(),
                "require_evidence": self.require_evidence, "auto_repair": self.auto_repair,
                "max_repair_attempts": self.max_repair_attempts}