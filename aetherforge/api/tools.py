'''
AI Control Tools - all callable operations for the engine.
'''
import json, sys, inspect
from typing import Optional, Any, Dict
from aetherforge.core import SemanticEntity, Rule, Quest, QuestStep, NPCBehavior
from aetherforge.core import RuleTriggerType, BehaviorType



def tool(desc=""):
    """Decorator: mark a method as a callable tool with description."""
    def decorator(func):
        func.__tool_desc__ = desc
        return func
    return decorator
class ToolResult:
    """Unified return type for all engine tools."""
    def __init__(self, ok: bool = True, data: Optional[Dict] = None, error: Optional[str] = None) -> None:
        self.success: bool = ok
        self.data: Dict = data or {}
        self.error: Optional[str] = error
    def to_dict(self) -> Dict:
        return {'success': self.success, 'data': self.data, 'error': self.error}
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class EngineTools:
    def __init__(self, world):
        self.world = world
        self._tool_cache = None

    @tool(desc="Create semantically-described entity")
    def create_entity(self, semantic_type='generic', name='', description='',
                      capabilities=None, requires=None, state=None, desc=None,
                      relationships=None, position=None, size=None,
                      visual=None, tags=None, editable_properties=None):
        try:
            # Alias: desc -> description
            if desc is not None and not description:
                description = desc
            e = SemanticEntity(
                semantic_type=semantic_type, name=name, description=description,
                capabilities=capabilities or [], requires=requires or {},
                state=state or {}, relationships=relationships or [],
                position=position or {'x':0,'y':0},
                size=size or {'width':32,'height':32},
                visual=visual or {'color':'#888','shape':'rectangle'},
                tags=tags or [],
                editable_properties=editable_properties or ['position','state'],
            )
            eid = self.world.create_entity(e)
            return ToolResult(True, {'entity_id': eid, 'entity': e.to_dict()})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Modify entity properties")
    def modify_entity(self, entity_id, changes):
        ok = self.world.modify_entity(entity_id, changes)
        if ok:
            ent = self.world.get_entity(entity_id)
            return ToolResult(True, {'entity_id': entity_id, 'entity': ent.to_dict() if ent else {}})
        return ToolResult(False, error=f'Entity {entity_id} not found')

    @tool(desc="Remove entity")
    def remove_entity(self, entity_id):
        ok = self.world.remove_entity(entity_id)
        return ToolResult(ok, {'entity_id': entity_id}) if ok else ToolResult(False, error=f'Entity {entity_id} not found')

    @tool(desc="Get entity details")
    def get_entity(self, entity_id):
        ent = self.world.get_entity(entity_id)
        if ent:
            return ToolResult(True, ent.to_dict())
        return ToolResult(False, error=f'Entity {entity_id} not found')

    @tool(desc="Query entities by type/tag/capability")
    def find_entities(self, query='', **filters):
        if query:
            results = self.world.query(query)
        else:
            results = self.world.find_entities(**filters)
        return ToolResult(True, {'count': len(results), 'entities': [e.to_dict() for e in results]})

    @tool(desc="Create game rule (when/then)")
    def create_rule(self, when=None, then=None, trigger=None, action=None,
                    else_actions=None, trigger_type='interaction', cooldown=0.0, priority=0):
        try:
            # Alias support: trigger/action -> when/then
            if when is None and trigger is not None:
                when = trigger
            if then is None and action is not None:
                then = action
            from aetherforge.core import Rule
            rule = Rule(when=when or [], then=then or [], else_then=else_actions or [],
                        trigger_type=RuleTriggerType(trigger_type),
                        cooldown=cooldown, priority=priority)
            rid = self.world.add_rule(rule)
            return ToolResult(True, {'rule_id': rid, 'rule': rule.to_dict()})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Remove game rule")
    def remove_rule(self, rule_id):
        ok = self.world.remove_rule(rule_id)
        return ToolResult(ok, {'rule_id': rule_id}) if ok else ToolResult(False, error=f'Rule {rule_id} not found')

    @tool(desc="Create quest with steps")
    def create_quest(self, name='', description='', steps=None,
                     rewards=None, prerequisites=None):
        try:
            step_fields = {k for k in QuestStep.__dataclass_fields__}
            qs = [QuestStep(**{k:v for k,v in s.items() if k in step_fields}) for s in (steps or [])]
            q = Quest(name=name, description=description, steps=qs,
                      rewards=rewards or [], prerequisites=prerequisites or [])
            qid = self.world.create_quest(q)
            return ToolResult(True, {'quest_id': qid, 'quest': q.to_dict()})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Complete a quest step")
    def complete_quest_step(self, quest_id, step_id):
        ok = self.world.complete_quest_step(quest_id, step_id)
        return ToolResult(ok, {'quest_id': quest_id, 'step_id': step_id}) if ok else ToolResult(False, error='Step not found')

    @tool(desc="Update quest state (active/completed/failed)")
    def update_quest_state(self, quest_id, state):
        ok = self.world.update_quest_state(quest_id, state)
        return ToolResult(ok, {'quest_id': quest_id, 'state': state}) if ok else ToolResult(False, error='Quest not found')

    @tool(desc="Set NPC behavior")
    def set_behavior(self, entity_id, behavior_type='goal_oriented',
                     goals=None, fallback='idle', speed=60.0, perception_range=200.0):
        try:
            b = NPCBehavior(entity_id=entity_id, behavior_type=BehaviorType(behavior_type),
                           goals=goals or [], fallback_action=fallback,
                           speed=speed, perception_range=perception_range)
            self.world.set_behavior(b)
            return ToolResult(True, {'entity_id': entity_id, 'behavior': b.to_dict()})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Set weather (clear/rainy/stormy/snowy)")
    def set_weather(self, weather):
        self.world.set_weather(weather)
        return ToolResult(True, {'weather': weather})

    @tool(desc="Set player entity by ID")
    def set_player(self, entity_id):
        ok = self.world.set_player(entity_id)
        return ToolResult(True, {'player_entity_id': entity_id}) if ok else ToolResult(False, error=f'Entity {entity_id} not found')

    @tool(desc="Trigger game event")
    def trigger_event(self, event_type, event_data=None):
        from aetherforge.core.rules import RuleEngine
        re = RuleEngine(self.world)
        results = re.evaluate(event_type, event_data or {})
        return ToolResult(True, {'event_type': event_type, 'rules_fired': len(results), 'results': results})

    @tool(desc="Read project summary")
    def read_project(self):
        return ToolResult(True, {'summary': self.world.summary, 'snapshot': self.world.snapshot().to_dict()})

    @tool(desc="Get full world snapshot as JSON")
    def observe(self, include_logs=True):
        d = self.world.snapshot().to_dict()
        if not include_logs:
            d['logs'] = []
        return ToolResult(True, d)

    @tool(desc="Commit changes to world with optional message")
    def commit_change(self, message=None):
        self.world.commit()
        return ToolResult(True, {'message': message or 'Changes committed', 'label': message})

    @tool(desc="Rollback last change")
    def rollback_change(self):
        ok = self.world.rollback()
        return ToolResult(ok, {'message': 'Rolled back'}) if ok else ToolResult(False, error='No checkpoint')

    @tool(desc="Configure audio settings")
    def set_audio(self, config):
        cid = self.world.set_audio_config(config)
        return ToolResult(True, {'audio_config_id': cid, 'config': config})

    @tool(desc="Set art direction intent")
    def set_art_intent(self, intent):
        aid = self.world.set_art_intent(intent)
        return ToolResult(True, {'art_intent_id': aid, 'intent': intent})

    def _discover_tools(self):
        """Cache tool list from @tool decorated methods via reflection."""
        tools = []
        for _name, _method in inspect.getmembers(self, predicate=inspect.ismethod):
            _desc = getattr(_method, '__tool_desc__', None)
            if _desc is not None:
                tools.append({'name': _name, 'desc': _desc})
        self._tool_cache = tools
    def list_tools(self):
        """Return cached tool list, lazy-discover if needed."""
        if self._tool_cache is None:
            self._discover_tools()
        return ToolResult(True, {'tools': (self._tool_cache or [])})

    @tool(desc="Save project to file path")
    def save_project(self, path):
        from aetherforge.tools import validate_project_path as _vpp
        ok, err = _vpp(path)
        if not ok:
            return ToolResult(False, error=err)
        try:
            self.world.save_to_file(path)
            return ToolResult(True, {'path': path})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Load project from file path")
    def load_project(self, path):
        from aetherforge.tools import validate_project_path as _vpp
        ok, err = _vpp(path)
        if not ok:
            return ToolResult(False, error=err)
        if not os.path.exists(os.path.normpath(path)):
            return ToolResult(False, error='File not found')
        try:
            self.world.load_from_file(path)
            return ToolResult(True, {'path': path, 'summary': self.world.summary})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Create a blank project with directory structure")
    def create_project(self, name, root_path):
        import os, json, time
        try:
            root = os.path.normpath(os.path.join(root_path, name))
            dirs = ['scenes', 'assets', 'scripts', 'tests', 'saves']
            for d in dirs:
                os.makedirs(os.path.join(root, d), exist_ok=True)
            scene_data = '{"camera":{"x":0,"y":0,"zoom":1.0},"entities":[],"entityCount":0}'
            with open(os.path.join(root, 'scenes', 'main.scene'), 'w', encoding='utf-8') as f:
                f.write(scene_data)
            meta = {'name': name, 'version': '1.0.0',
                    'createdAt': int(time.time() * 1000),
                    'modifiedAt': int(time.time() * 1000),
                    'sceneCount': 1, 'recentScenes': ['main.scene']}
            with open(os.path.join(root, 'project.json'), 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            self.world.project_root = root
            return ToolResult(True, {'name': name, 'root': root, 'dirs': dirs})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Create a new scene file in the current project")
    def create_scene(self, scene_name):
        import os
        if not getattr(self.world, 'project_root', None):
            return ToolResult(False, error='No project open. Call create_project first.')
        scenes_dir = os.path.join(self.world.project_root, 'scenes')
        scene_file = scene_name if scene_name.endswith('.scene') else scene_name + '.scene'
        path = os.path.join(scenes_dir, scene_file)
        if os.path.exists(path):
            return ToolResult(False, error='Scene already exists: ' + scene_name)
        data = '{"camera":{"x":0,"y":0,"zoom":1.0},"entities":[],"entityCount":0}'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(data)
        return ToolResult(True, {'scene': scene_name, 'path': path})

    @tool(desc="List all scene files in the current project")
    def list_scenes(self):
        import os, glob
        if not getattr(self.world, 'project_root', None):
            return ToolResult(False, error='No project open')
        scenes_dir = os.path.join(self.world.project_root, 'scenes')
        files = sorted(glob.glob(os.path.join(scenes_dir, '*.scene')))
        scenes = [os.path.splitext(os.path.basename(f))[0] for f in files]
        return ToolResult(True, {'scenes': scenes, 'count': len(scenes)})

    @tool(desc="Start the game runtime loop")
    def start_runtime(self):
        from aetherforge.runtime.game_loop import GameRuntime
        self.runtime = GameRuntime(self.world)
        self.runtime.start()
        return ToolResult(True, {'status': 'running', 'tick': 0})

    @tool(desc="Pause the game runtime")
    def pause_runtime(self):
        if not self.runtime:
            return ToolResult(False, error='Runtime not started')
        self.runtime.paused = True
        return ToolResult(True, {'status': 'paused', 'tick': self.world.tick})

    @tool(desc="Resume the game runtime")
    def resume_runtime(self):
        if not self.runtime:
            return ToolResult(False, error='Runtime not started')
        self.runtime.paused = False
        return ToolResult(True, {'status': 'running', 'tick': self.world.tick})

    @tool(desc="Stop the game runtime")
    def stop_runtime(self):
        if not self.runtime:
            return ToolResult(False, error='Runtime not started')
        self.runtime = None
        return ToolResult(True, {'status': 'stopped'})

    @tool(desc="Advance one frame in the game loop")
    def step_frame(self, dt=0.016):
        if not self.runtime:
            return ToolResult(False, error='Runtime not started')
        result = self.runtime.tick(dt)
        return ToolResult(True, {'tick': self.world.tick, 'result': result})

    @tool(desc="Set the runtime time scale (0.0 to 10.0)")
    def set_time_scale(self, scale=1.0):
        if not self.runtime:
            return ToolResult(False, error='Runtime not started')
        self.runtime.time_scale = max(0.0, min(10.0, scale))
        return ToolResult(True, {'time_scale': self.runtime.time_scale})

    @tool(desc="Get current runtime state")
    def get_runtime_state(self):
        if not self.runtime:
            return ToolResult(True, {'running': False})
        return ToolResult(True, {
            'running': True,
            'paused': getattr(self.runtime, 'paused', False),
            'time_scale': getattr(self.runtime, 'time_scale', 1.0),
            'tick': self.world.tick,
        })

    @tool(desc="Register an input action with key bindings")
    def register_input(self, action, keys):
        if isinstance(keys, str):
            keys = [keys]
        mgr = getattr(self.world, '_input_manager', None)
        if mgr is None:
            from aetherforge.tools.input_manager import InputManager
            mgr = InputManager()
            self.world._input_manager = mgr
        mgr.bind(action, keys)
        return ToolResult(True, {'action': action, 'keys': keys})

    @tool(desc="Get current input state")
    def get_input_state(self):
        mgr = getattr(self.world, '_input_manager', None)
        if mgr is None:
            return ToolResult(True, {'inputs': {}})
        return ToolResult(True, {'inputs': mgr.get_state()})


    @tool(desc="Export project to distributable zip package")
    def export_project(self, project_root=None, output_path=None):
        import os
        root = project_root or getattr(self.world, 'project_root', None)
        if not root:
            return ToolResult(False, error='No project root set. Provide project_root or call create_project first.')
        from aetherforge.tools.exporter import export_project as _export
        result = _export(root, output_path, include_viewer=False)
        if result.get('success'):
            return ToolResult(True, result)
        return ToolResult(False, error=result.get('error', 'Export failed'))

    @tool(desc="Build standalone game package with embedded viewer")
    def build_project(self, project_root=None, output_path=None):
        import os
        root = project_root or getattr(self.world, 'project_root', None)
        if not root:
            return ToolResult(False, error='No project root set. Provide project_root or call create_project first.')
        from aetherforge.tools.exporter import build_project as _build
        result = _build(root, output_path)
        if result.get('success'):
            return ToolResult(True, result)
        return ToolResult(False, error=result.get('error', 'Build failed'))

    @tool(desc="List contents of an exported project package")
    def inspect_package(self, package_path):
        import zipfile, os
        if not os.path.isfile(package_path):
            return ToolResult(False, error='File not found: ' + package_path)
        try:
            with zipfile.ZipFile(package_path, 'r') as zf:
                names = zf.namelist()
            size = os.path.getsize(package_path)
            return ToolResult(True, {'path': package_path, 'size': size, 'file_count': len(names), 'files': names})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    @tool(desc="Validate project structure for export readiness")
    def validate_project(self, project_root=None):
        import os, json
        root = project_root or getattr(self.world, 'project_root', None)
        if not root:
            return ToolResult(False, error='No project root')
        issues = []
        warnings = []
        pj = os.path.join(root, 'project.json')
        if not os.path.isfile(pj):
            issues.append('Missing project.json')
        else:
            try:
                with open(pj, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                issues.append('project.json is not valid JSON')
        scenes_dir = os.path.join(root, 'scenes')
        if not os.path.isdir(scenes_dir):
            issues.append('Missing scenes/ directory')
        else:
            scene_files = [f for f in os.listdir(scenes_dir) if f.endswith('.scene')]
            if not scene_files:
                issues.append('No .scene files in scenes/')
        for d in ['assets', 'scripts']:
            dd = os.path.join(root, d)
            if os.path.isdir(dd) and not os.listdir(dd):
                warnings.append(d + '/ directory is empty')
        return ToolResult(True, {
            'ready': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'project_root': root,
        })    @tool(desc="Get a full snapshot of the game world")
    def observe_full(self):
        result = {
            'tick': self.world.tick,
            'game_time': getattr(self.world, 'game_time', 0.0),
            'weather': getattr(self.world, 'weather', 'clear'),
            'revision': getattr(self.world, 'revision', 0),
            'entity_count': len(self.world.entities),
            'rules_count': len(getattr(self.world, 'rules', {})),
        }
        if self.runtime:
            result['runtime'] = {
                'running': True,
                'paused': getattr(self.runtime, 'paused', False),
                'time_scale': getattr(self.runtime, 'time_scale', 1.0),
                'tick': self.world.tick,
            }
        result['entities'] = [
            {'id': eid, 'name': getattr(e, 'name', ''),
             'type': getattr(e, 'semantic_type', 'generic')}
            for eid, e in self.world.entities.items()
        ]
        return ToolResult(True, result)
