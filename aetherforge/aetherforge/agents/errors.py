"""Agent Runtime custom exceptions. All agent-related errors inherit from AetherForgeAgentError."""

class AetherForgeAgentError(Exception):
    """Base exception for all Agent Runtime errors."""
    pass

class EvidenceError(AetherForgeAgentError):
    """Raised when evidence validation fails."""
    pass

class CommitGateError(AetherForgeAgentError):
    """Raised when commit is rejected by the gate."""
    pass

class TokenBudgetExceeded(AetherForgeAgentError):
    """Raised when token budget is exhausted."""
    pass

class PermissionDenied(AetherForgeAgentError):
    """Raised when an agent lacks permission for a tool."""
    pass

class TransactionError(AetherForgeAgentError):
    """Raised when a transaction operation fails."""
    pass

class ModelRouterError(AetherForgeAgentError):
    """Raised when model API call fails."""
    pass

class ValidationError(AetherForgeAgentError):
    """Raised when validation fails."""
    pass