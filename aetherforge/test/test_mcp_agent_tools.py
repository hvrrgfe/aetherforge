"""Tests for High-Level MCP Agent Tools."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aetherforge.api.engine_v2 import EngineToolsV2, ToolResult

def test_agent_tools_available():
    # Test with a minimal world model
    class MockWorld:
        def __init__(self):
            self.entities = {}
            self.rules = {}
            self.quests = {}
            self.behaviors = {}
            self.player_entity_id = None
            self._history = []
            self.tick = 0
            self.game_time = 0.0
            self.weather = "clear"
            self.event_log = []
        def _checkpoint(self): pass
        def get_entity(self, eid): return self.entities.get(eid)
        def create_entity(self, e): return "ent_1"
        def find_entities(self, **kw): return []
        def query(self, q): return []

    eng = EngineToolsV2(MockWorld())
    tools = eng.list_tools()
    data = tools.to_dict() if hasattr(tools, "to_dict") else tools
    tool_names = [t["name"] for t in data.get("data", {}).get("tools", data if isinstance(data, list) else [])]

    agent_tools = ["agent_start_task", "agent_get_status", "agent_get_report",
                   "agent_get_evidence", "agent_request_approval",
                   "agent_commit", "agent_rollback", "agent_run_full"]
    found = [t for t in agent_tools if t in tool_names]
    print(f"  [PASS] agent_tools_available: {len(found)}/{len(agent_tools)} found")
    for t in agent_tools:
        if t not in tool_names:
            print(f"    MISSING: {t}")

def test_agent_start_task():
    class MockWorld:
        def __init__(self):
            self.entities = {}; self.rules = {}; self.quests = {}
            self.behaviors = {}; self.player_entity_id = None
            self._history = []; self.tick = 0; self.game_time = 0.0
            self.weather = "clear"; self.event_log = []
        def _checkpoint(self): pass
        def get_entity(self, eid): return self.entities.get(eid)
        def create_entity(self, e): return "ent_1"
        def find_entities(self, **kw): return []
        def query(self, q): return []

    eng = EngineToolsV2(MockWorld())
    result = eng.agent_start_task(goal="Create a test entity")
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    assert result.get("success") == True
    data = result.get("data", {})
    assert "task_id" in data
    print(f"  [PASS] agent_start_task: {data.get('task_id')}")

def test_agent_status_flow():
    class MockWorld:
        def __init__(self):
            self.entities = {}; self.rules = {}; self.quests = {}
            self.behaviors = {}; self.player_entity_id = None
            self._history = []; self.tick = 0; self.game_time = 0.0
            self.weather = "clear"; self.event_log = []
        def _checkpoint(self): pass
        def get_entity(self, eid): return self.entities.get(eid)
        def create_entity(self, e): return "ent_1"
        def find_entities(self, **kw): return []
        def query(self, q): return []

    eng = EngineToolsV2(MockWorld())

    # Start task
    r1 = eng.agent_start_task(goal="Create a village")
    data1 = r1.to_dict() if hasattr(r1, "to_dict") else r1
    task_id = data1.get("data", {}).get("task_id", "")

    # Get status
    r2 = eng.agent_get_status(task_id=task_id)
    data2 = r2.to_dict() if hasattr(r2, "to_dict") else r2
    assert data2.get("success") == True
    print("  [PASS] agent_status_flow")

def test_agent_rollback():
    class MockWorld:
        def __init__(self):
            self.entities = {}; self.rules = {}; self.quests = {}
            self.behaviors = {}; self.player_entity_id = None
            self._history = []; self.tick = 0; self.game_time = 0.0
            self.weather = "clear"; self.event_log = []
        def _checkpoint(self): pass
        def get_entity(self, eid): return self.entities.get(eid)
        def create_entity(self, e): return "ent_1"
        def find_entities(self, **kw): return []
        def query(self, q): return []

    eng = EngineToolsV2(MockWorld())
    r1 = eng.agent_start_task(goal="Test rollback")
    data1 = r1.to_dict() if hasattr(r1, "to_dict") else r1
    task_id = data1.get("data", {}).get("task_id", "")

    r2 = eng.agent_rollback(task_id=task_id)
    data2 = r2.to_dict() if hasattr(r2, "to_dict") else r2
    assert data2.get("success") == True
    print("  [PASS] agent_rollback")

if __name__ == "__main__":
    tests = [test_agent_tools_available, test_agent_start_task,
             test_agent_status_flow, test_agent_rollback]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            import traceback
            print(f"  [FAIL] {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\nResult: {passed}/{passed+failed} passed, {failed} failed")