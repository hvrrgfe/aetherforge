'''
AI Control Tools - all callable operations for the engine.
'''
import json, sys
sys.path.insert(0, '.')
from aetherforge.core import SemanticEntity, Rule, Quest, QuestStep, NPCBehavior
from aetherforge.core import RuleTriggerType, BehaviorType

class ToolResult:
    def __init__(self, ok=True, data=None, error=None):
        self.success = ok
        self.data = data or {}
        self.error = error
    def to_dict(self):
        return {'success': self.success, 'data': self.data, 'error': self.error}
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class EngineTools:
    def __init__(self, world):
        self.world = world

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

    def modify_entity(self, entity_id, changes):
        ok = self.world.modify_entity(entity_id, changes)
        if ok:
            ent = self.world.get_entity(entity_id)
            return ToolResult(True, {'entity_id': entity_id, 'entity': ent.to_dict() if ent else {}})
        return ToolResult(False, error=f'Entity {entity_id} not found')

    def remove_entity(self, entity_id):
        ok = self.world.remove_entity(entity_id)
        return ToolResult(ok, {'entity_id': entity_id}) if ok else ToolResult(False, error=f'Entity {entity_id} not found')

    def get_entity(self, entity_id):
        ent = self.world.get_entity(entity_id)
        if ent:
            return ToolResult(True, ent.to_dict())
        return ToolResult(False, error=f'Entity {entity_id} not found')

    def find_entities(self, query='', **filters):
        if query:
            results = self.world.query(query)
        else:
            results = self.world.find_entities(**filters)
        return ToolResult(True, {'count': len(results), 'entities': [e.to_dict() for e in results]})

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

    def remove_rule(self, rule_id):
        ok = self.world.remove_rule(rule_id)
        return ToolResult(ok, {'rule_id': rule_id}) if ok else ToolResult(False, error=f'Rule {rule_id} not found')

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

    def complete_quest_step(self, quest_id, step_id):
        ok = self.world.complete_quest_step(quest_id, step_id)
        return ToolResult(ok, {'quest_id': quest_id, 'step_id': step_id}) if ok else ToolResult(False, error='Step not found')

    def update_quest_state(self, quest_id, state):
        ok = self.world.update_quest_state(quest_id, state)
        return ToolResult(ok, {'quest_id': quest_id, 'state': state}) if ok else ToolResult(False, error='Quest not found')

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

    def set_weather(self, weather):
        self.world.set_weather(weather)
        return ToolResult(True, {'weather': weather})

    def set_player(self, entity_id):
        ok = self.world.set_player(entity_id)
        return ToolResult(True, {'player_entity_id': entity_id}) if ok else ToolResult(False, error=f'Entity {entity_id} not found')

    def trigger_event(self, event_type, event_data=None):
        from aetherforge.core.rules import RuleEngine
        re = RuleEngine(self.world)
        results = re.evaluate(event_type, event_data or {})
        return ToolResult(True, {'event_type': event_type, 'rules_fired': len(results), 'results': results})

    def read_project(self):
        return ToolResult(True, {'summary': self.world.summary, 'snapshot': self.world.snapshot().to_dict()})

    def observe(self, include_logs=True):
        d = self.world.snapshot().to_dict()
        if not include_logs:
            d['logs'] = []
        return ToolResult(True, d)

    def commit_change(self):
        self.world.commit()
        return ToolResult(True, {'message': 'Changes committed'})

    def rollback_change(self):
        ok = self.world.rollback()
        return ToolResult(ok, {'message': 'Rolled back'}) if ok else ToolResult(False, error='No checkpoint')

    def set_audio(self, config):
        cid = self.world.set_audio_config(config)
        return ToolResult(True, {'audio_config_id': cid, 'config': config})

    def set_art_intent(self, intent):
        aid = self.world.set_art_intent(intent)
        return ToolResult(True, {'art_intent_id': aid, 'intent': intent})

    def list_tools(self):
        return ToolResult(True, {'tools': [
            {'name':'create_entity','desc':'Create semantically-described entity'},
            {'name':'modify_entity','desc':'Modify entity properties'},
            {'name':'remove_entity','desc':'Remove entity'},
            {'name':'get_entity','desc':'Get entity details'},
            {'name':'find_entities','desc':'Query entities'},
            {'name':'create_rule','desc':'Create game rule'},
            {'name':'remove_rule','desc':'Remove game rule'},
            {'name':'create_quest','desc':'Create quest'},
            {'name':'complete_quest_step','desc':'Complete quest step'},
            {'name':'update_quest_state','desc':'Update quest state (active/completed/failed)'},
            {'name':'set_behavior','desc':'Set NPC behavior'},
            {'name':'set_weather','desc':'Set weather'},
            {'name':'set_player','desc':'Set player entity'},
            {'name':'read_project','desc':'Read project summary'},
            {'name':'trigger_event','desc':'Trigger game event'},
            {'name':'commit_change','desc':'Commit changes'},
            {'name':'rollback_change','desc':'Rollback changes'},
            {'name':'set_audio','desc':'Configure audio'},
            {'name':'set_art_intent','desc':'Set art intent'},
            {'name':'observe','desc':'Get world snapshot'},
            {'name':'list_tools','desc':'List all tools'},
            {'name':'save_project','desc':'Save project to file'},
            {'name':'load_project','desc':'Load project from file'},
        ]})

    def save_project(self, path):
        try:
            self.world.save_to_file(path)
            return ToolResult(True, {'path': path})
        except Exception as ex:
            return ToolResult(False, error=str(ex))

    def load_project(self, path):
        try:
            self.world.load_from_file(path)
            return ToolResult(True, {'path': path, 'summary': self.world.summary})
        except Exception as ex:
            return ToolResult(False, error=str(ex))
