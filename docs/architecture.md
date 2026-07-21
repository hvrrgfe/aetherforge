# AetherForge Agent Runtime Architecture

## Overview
AetherForge is an AI-native game engine upgraded with a multi-agent runtime system.
Adds evidence-based verification, transaction management, and autonomous agent collaboration.

## Architecture Layers

### 1. Agent Runtime (NEW - Python)
```
agents/
  protocol.py      - Core types: Evidence, Claim, TaskState, AgentTransaction
  state.py         - AgentStateManager, world_revision tracking
  errors.py        - Custom exceptions
  gateway.py       - ToolGateway: permission + evidence capture
  orchestrator.py  - AgentOrchestrator: task lifecycle, agent coordination
  model_router.py  - ModelRouter: OpenAI-compatible API abstraction
  context.py       - ContextManager: incremental context building
  policies.py      - AgentPolicy, TokenBudget
  roles/           - Explorer, Planner, Builder, Verifier, Critic

validation/
  evidence.py      - EvidenceStore: immutable evidence chain
  commit_gate.py   - CommitGate: transaction commit policy
  assertions.py    - AssertionEngine: deterministic state checks
  scene_tests.py   - SceneTestRunner: automated tests
  invariants.py    - InvariantChecker: consistency checks
  consistency.py   - ConsistencyValidator: semantic checks

runtime/
  transaction.py   - TransactionManager: BEGIN/COMMIT/ROLLBACK
  permissions.py   - PermissionManager: role-based access control
```

### 2. Desktop Client (NEW - WinUI 3 C#)
```
AetherForgeStudio-WinUI/
  Pages/           - Dashboard, AgentWorkspace, WorldViewer, Verification
  Controls/        - AgentStatusCard, EvidencePanel, TransactionBar
  Services/        - AetherForgeApiService, AgentStateService
  Models/          - TaskInfo, AgentState, WorldSnapshot
```

### 3. Existing Engine (Python)
- WorldModel, EngineTools, EngineToolsV2, MCP Server (67 tools)

## Data Flow
```
User -> AgentOrchestrator -> Explorer -> Planner -> Builder
  -> Verifier -> Critic -> CommitGate -> Committed/Rolled Back
```

## Key Decisions
1. Evidence immutable: created only by ToolGateway from real tool calls
2. Builder cannot call commit/rollback: blocked by PermissionManager
3. Verifier reads engine state directly: no trust of Builder summaries
4. Transactions use WorldModel checkpoint snapshots for rollback
5. Token budget: hard limit enforced, graceful suspension
6. All agent communication uses structured JSON

## Test Coverage: 83 Tests
- test_security.py: 22 | test_evidence.py: 10 | test_gateway.py: 8
- test_transaction.py: 8 | test_validation.py: 8 | test_roles.py: 10
- test_token_budget.py: 6 | test_mcp_agent_tools.py: 4 | test_e2e_agent.py: 7
