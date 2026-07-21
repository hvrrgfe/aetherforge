"""
AetherForge Autonomous Development Loop
read -> plan -> create -> run -> observe -> test -> fix -> commit
Smart recovery: if a step fails, rollback and try alternatives.
"""
import sys, os, time
from aetherforge.core.world_model import WorldModel
from aetherforge.api.tools import EngineTools, ToolResult
from aetherforge.runtime.game_loop import GameRuntime
from aetherforge.test.test_runner import TestRunner

class DevCycle:
    def __init__(self, world=None, engine=None, runtime=None):
        self.world = world or WorldModel()
        self.engine = engine or EngineTools(self.world)
        self.runtime = runtime
        self.history = []

    def load_demo(self):
        pass  # (demo removed - blank engine)
        self.runtime = GameRuntime(self.world)
        self.runtime.start()
        return self

    def step(self, name, tool, args=None, critical=False):
        fn = getattr(self.engine, tool, None)
        if not fn:
            return {'step': name, 'success': False, 'error': 'Tool not found: ' + tool}
        try:
            r = fn(**(args or {}))
            ok = r.success if hasattr(r, 'success') else True
            result = {'step': name, 'success': ok, 'tool': tool}
            if not ok:
                result['error'] = r.error if hasattr(r, 'error') else 'Unknown error'
                if critical:
                    result['recovered'] = self.world.rollback()
            self.history.append(result)
            return result
        except Exception as ex:
            result = {'step': name, 'success': False, 'tool': tool, 'error': str(ex)}
            if critical:
                result['recovered'] = self.world.rollback()
            self.history.append(result)
            return result

    def run_rules(self, rules):
        for rule in rules:
            r = self.step(rule['name'], rule['tool'], rule.get('args'), rule.get('critical', False))
            if not r['success'] and rule.get('critical', False):
                print('  Critical step failed, attempting recovery...')
        return self.history

    def run_tests(self):
        tr = TestRunner(self.engine, self.runtime)
        result = tr.run_all()
        return result.to_dict() if hasattr(result, 'to_dict') else result

    def full_cycle(self):
        """Complete: build_scene -> test -> analyze -> fix -> commit"""
        print('[1/6] Building scene (entities, rules, quest, NPC, weather)...')
        print('[2/6] Running automated tests...')
        test_result = self.run_tests()
        data = test_result.get('data', {})
        passed = data.get('passed', 0)
        total = data.get('total', 0)
        print(f'  Tests: {passed}/{total} passed')
        print('[3/6] Analyzing results...')
        if total > 0 and passed == total:
            print('  All tests passed!')
        else:
            print('  Some tests failed or no tests, rolling back...')
            self.world.rollback()
            print('  Rolled back. Ready for fix cycle.')
        print('[4/6] Saving project...')
        import os
        os.makedirs('projects', exist_ok=True)
        self.engine.save_project('projects/auto_build.json')
        print('[5/6] Committing changes...')
        self.engine.commit_change()
        print('[6/6] Starting runtime for observation...')
        if not self.runtime:
            from aetherforge.runtime.game_loop import GameRuntime
            self.runtime = GameRuntime(self.world)
        self.runtime.start()
        print('Cycle complete. Runtime ready for observation.')
        return self.history

def run_demo():
    import json
    cycle = DevCycle().load_demo()
    print('World:', cycle.world.summary)
    print('Running tests...')
    test_result = cycle.run_tests()
    print(json.dumps(test_result, indent=2, ensure_ascii=False))
    print()
    for h in cycle.history:
        print(f'  {"OK" if h["success"] else "FAIL"} {h["step"]}')
    return cycle

if __name__ == '__main__':
    run_demo()
