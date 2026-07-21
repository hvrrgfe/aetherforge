"""Tests for Token Budget and Repair Loop."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aetherforge.agents.policies import TokenBudget, AgentPolicy, ApprovalMode

# --- Token Budget Tests ---

def test_token_budget_defaults():
    tb = TokenBudget()
    assert tb.max_tokens == 4000
    assert tb.used_tokens == 0
    assert not tb.exhausted
    assert not tb.warning
    print("  [PASS] token_budget_defaults")

def test_token_budget_use():
    tb = TokenBudget(max_tokens=1000)
    assert tb.use(500) == True
    assert tb.used_tokens == 500
    assert not tb.exhausted
    assert tb.remaining == 500
    print("  [PASS] token_budget_use")

def test_token_budget_exhaustion():
    tb = TokenBudget(max_tokens=100)
    tb.use(80)
    assert tb.warning  # 80 >= 80 (100*0.8)
    tb.use(20)
    assert tb.exhausted
    assert tb.use(10) == False  # hard limit
    print("  [PASS] token_budget_exhaustion")

def test_token_budget_no_hard_limit():
    tb = TokenBudget(max_tokens=100, hard_limit=False)
    tb.use(120)
    assert tb.exhausted == False
    print("  [PASS] token_budget_no_hard_limit")

# --- Agent Policy Tests ---

def test_agent_policy_defaults():
    p = AgentPolicy()
    assert p.max_retries == 3
    assert p.require_evidence == True
    dump = p.to_dict()
    assert "token_budget" in dump
    print("  [PASS] agent_policy_defaults")

# --- Repair Logic Tests ---

def test_critic_repair_suggestions():
    from aetherforge.agents.roles import Critic
    from aetherforge.agents.gateway import ToolGateway
    from aetherforge.runtime.permissions import AgentRole

    class MockEngine:
        def observe(self): return {"success": True, "data": {}}
        def list_tools(self): return {"success": True, "data": {"tools": []}}

    eng = MockEngine()
    gw = ToolGateway(eng)
    gw.set_role(AgentRole.CRITIC)
    crit = Critic(gw)

    # Test with world that has issues
    class MockWorld:
        def __init__(self):
            self.entities = {"e1": type("E", (), {"name": ""})()}
            self.rules = {}
            self.quests = {}
            self.behaviors = {}

    world = MockWorld()
    review = crit.review("task_1", world)
    assert review["total_issues"] > 0
    repair_plan = crit.generate_repair_plan(review["issues"])
    assert len(repair_plan) >= 1
    print(f"  [PASS] critic_repair_suggestions: {len(repair_plan)} repairs")

if __name__ == "__main__":
    tests = [test_token_budget_defaults, test_token_budget_use, test_token_budget_exhaustion,
             test_token_budget_no_hard_limit, test_agent_policy_defaults,
             test_critic_repair_suggestions]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\nResult: {passed}/{passed+failed} passed, {failed} failed")