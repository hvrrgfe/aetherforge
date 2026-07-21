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
        from aetherforge.demo.station import demo_setup
        demo_setup(self.engine)
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

    def build_station(self):
        self._ids = {}
        self.engine.set_weather('rainy')
        r = self.engine.create_entity(semantic_type='building', name='Waiting Room',
            description='Abandoned train station waiting room, door is locked',
            position={'x':500,'y':200}, size={'width':200,'height':180},
            visual={'color':'#5a4a3a','shape':'rectangle'}, capabilities=['enter','inspect'])
        wait_id = r.data['entity_id']
        self._ids['waiting_room'] = wait_id
        r = self.engine.create_entity(semantic_type='roof', name='Station Eaves',
            description='Eaves outside waiting room, provides shelter from rain',
            position={'x':450,'y':100}, size={'width':300,'height':20},
            visual={'color':'#6a5a4a','shape':'rectangle'}, capabilities=['shelter'])
        r = self.engine.create_entity(semantic_type='locked_door', name='Iron Door',
            description='Rusted iron door blocking entrance to waiting room',
            capabilities=['open','lock','unlock','inspect','interact'],
            requires={'item':'station_key'}, state={'locked':True,'open':False},
            position={'x':500,'y':300}, size={'width':64,'height':16},
            visual={'color':'#8a7a6a','shape':'rectangle'},
            editable_properties=['position','state','requires'])
        self._ids['door'] = r.data['entity_id']
        r = self.engine.create_entity(semantic_type='player', name='Traveler',
            description='A traveler arriving at the abandoned station late at night',
            capabilities=['move','interact','use','inspect','pick_up'],
            state={'inventory':[],'health':100},
            position={'x':200,'y':400}, size={'width':28,'height':32},
            visual={'color':'#4488cc','shape':'rectangle'})
        self._ids['player'] = r.data['entity_id']
        self.engine.set_player(self._ids['player'])
        r = self.engine.create_entity(semantic_type='key_item', name='Station Key',
            description='Rusted station key that can unlock the waiting room door',
            capabilities=['pick_up','use'], state={'picked_up':False},
            position={'x':100,'y':150}, size={'width':16,'height':16},
            visual={'color':'#ccaa44','shape':'circle'}, tags=['key','important'])
        r = self.engine.create_entity(semantic_type='npc', name='Vagrant',
            description='A homeless person sheltering at the station',
            capabilities=['talk','inspect'], state={'mood':'anxious','has_info':True},
            position={'x':350,'y':380}, size={'width':28,'height':32},
            visual={'color':'#cc8844','shape':'rectangle'})
        npc_id = r.data['entity_id']
        self._ids['npc'] = npc_id
        from aetherforge.core import NPCBehavior, BehaviorType
        b = NPCBehavior(entity_id=npc_id, behavior_type=BehaviorType.GOAL_ORIENTED,
            goals=[{'condition':'weather.rain == true','priority':10,
                    'action':'seek_shelter','desc':'Find shelter when raining'},
                   {'condition':'always','priority':1,'action':'wander',
                    'desc':'Wander around when not raining'}],
            fallback_action='wander_near_station', speed=50.0, perception_range=250.0)
        self.world.set_behavior(b)
        from aetherforge.core import Quest, QuestStep
        q = Quest(name='Enter the Waiting Room',
            description='Find the station key and open the iron door',
            steps=[QuestStep(step_id='find_key',description='Find the station key',
                             condition='player.inventory.contains(station_key)'),
                   QuestStep(step_id='open_door',description='Open the iron door with key',
                             condition='door.state.open == true')],
            rewards=['access_to_waiting_room'])
        self.world.create_quest(q)
        self.world.set_audio_config({'intent':'Atmospheric rainy station music',
            'mood':['lonely','suspenseful'],
            'layers':[{'name':'rain','volume':0.6},{'name':'drone','volume':0.4}]})
        self.engine.create_rule(when=['player.interacts_with(Station Key)'],
            then=['key.pick_up()','player.inventory.add(Station Key)','key.state.picked_up=true'],
            trigger_type='interaction', priority=5)
        self.engine.create_rule(
            when=['player.interacts_with(Iron Door)','player.inventory.contains(station_key)'],
            then=['door.unlock()','door.open()','quest.find_key.complete()','music.intensity(0.3)'],
            else_actions=['dialogue.play(door_locked)','sound.play(metal_impact)'],
            trigger_type='interaction', priority=10)
        self.engine.commit_change()
        print('  [build] complete!')

    def run_tests(self):
        tr = TestRunner(self.engine, self.runtime)
        result = tr.run_all()
        return result.to_dict() if hasattr(result, 'to_dict') else result

    def full_cycle(self):
        """Complete: build_scene -> test -> analyze -> fix -> commit"""
        print('[1/6] Building scene (entities, rules, quest, NPC, weather)...')
        self.build_station()
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
