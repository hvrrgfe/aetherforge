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
                      capabilities=None, requires=None, state=None,
                      relationships=None, position=None, size=None,
                      visual=None, tags=None, editable_properties=None):
        try:
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
    def create_rule(self, when=None, then=None, else_actions=None,
                    trigger_type='interaction', cooldown=0.0, priority=0):
        try:
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
            qs = [QuestStep(**s) for s in (steps or [])]
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

    @tool(desc="Commit changes to world")
    def commit_change(self):
        self.world.commit()
        return ToolResult(True, {'message': 'Changes committed'})

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
