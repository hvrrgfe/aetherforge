'''
Semantic World Model - the core of AetherForge.
'''
import json, copy, time
from collections import deque
from pathlib import Path
from . import SemanticEntity, Rule, Quest, QuestStep, NPCBehavior, WorldSnapshot, RuleTriggerType

class WorldModel:
    def __init__(self):
        self.entities = {}
        self.rules = {}
        self.quests = {}
        self.behaviors = {}
        self.audio_configs = []
        self.art_intents = []
        self.player_entity_id = None
        self.tick = 0
        self.game_time = 0.0
        self.weather = 'clear'
        self.event_log = []
        self._history = deque(maxlen=100)

    def _checkpoint(self):
        state = {
            'entities': {eid: copy.deepcopy(e) for eid, e in self.entities.items()},
            'rules': copy.deepcopy(self.rules),
            'quests': copy.deepcopy(self.quests),
            'behaviors': copy.deepcopy(self.behaviors),
            'player_entity_id': self.player_entity_id,
            'weather': self.weather, 'game_time': self.game_time,
        }
        self._history.append(state)  # deque maxlen=100 auto-evicts

    def _log(self, etype, data):
        self.event_log.append({'type': etype, 'data': data, 'tick': self.tick, 'time': self.game_time})

    def create_entity(self, entity):
        self._checkpoint()
        self.entities[entity.entity_id] = entity
        self._log('entity_created', {'entity_id': entity.entity_id, 'name': entity.name})
        return entity.entity_id

    def modify_entity(self, entity_id, changes):
        if entity_id not in self.entities:
            return False
        self._checkpoint()
        ent = self.entities[entity_id]
        for key, val in changes.items():
            if hasattr(ent, key):
                if key == 'state' and isinstance(val, dict):
                    ent.state.update(val)
                else:
                    setattr(ent, key, val)
        self._log('entity_modified', {'entity_id': entity_id, 'changes': changes})
        return True

    def remove_entity(self, entity_id):
        if entity_id not in self.entities:
            return False
        self._checkpoint()
        if self.player_entity_id == entity_id:
            self.player_entity_id = None
        del self.entities[entity_id]
        self.behaviors.pop(entity_id, None)
        self._log('entity_removed', {'entity_id': entity_id})
        return True

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    def quick_modify_entity(self, entity_id, changes):
        """High-frequency mutate: skip checkpoint deepcopy."""
        ent = self.entities.get(entity_id)
        if not ent:
            return False
        for key, val in changes.items():
            if hasattr(ent, key):
                if key == 'state' and isinstance(val, dict):
                    ent.state.update(val)
                else:
                    setattr(ent, key, val)
        return True

    def quick_remove_entity(self, entity_id):
        """High-frequency remove: skip checkpoint deepcopy."""
        if entity_id not in self.entities:
            return False
        if self.player_entity_id == entity_id:
            self.player_entity_id = None
        del self.entities[entity_id]
        self.behaviors.pop(entity_id, None)
        return True

    def quick_create_entity(self, entity):
        """High-frequency create: skip checkpoint deepcopy."""
        self.entities[entity.entity_id] = entity
        return entity.entity_id

    def find_entities(self, **filters):
        results = list(self.entities.values())
        for key, val in filters.items():
            if key == 'semantic_type':
                results = [e for e in results if e.semantic_type == val]
            elif key == 'tag':
                results = [e for e in results if val in e.tags]
            elif key == 'capability':
                results = [e for e in results if val in e.capabilities]
        return results

    def query(self, q):
        """Query entities by type/tag/capability. Supports quoted values for spaces."""
        filters = {}
        import re as _re
        for match in _re.finditer(r'(\w+):("([^"]*)"|(\S+))', q):
            key = match.group(1)
            val = match.group(3) or match.group(4)
            if key == 'type':
                filters['semantic_type'] = val
            elif key == 'tag':
                filters['tag'] = val
            elif key == 'capability':
                filters['capability'] = val
        return self.find_entities(**filters)

    def add_rule(self, rule):
        self._checkpoint()
        self.rules[rule.rule_id] = rule
        self._log('rule_added', {'rule_id': rule.rule_id})
        return rule.rule_id

    def remove_rule(self, rule_id):
        if rule_id in self.rules:
            self._checkpoint()
            del self.rules[rule_id]
            self._log('rule_removed', {'rule_id': rule_id})
            return True
        return False

    def find_rules_by_trigger(self, trigger_type):
        return [r for r in self.rules.values() if r.trigger_type == trigger_type and r.enabled]

    def create_quest(self, quest):
        self._checkpoint()
        self.quests[quest.quest_id] = quest
        self._log('quest_created', {'quest_id': quest.quest_id, 'name': quest.name})
        return quest.quest_id

    def update_quest_state(self, quest_id, state):
        if quest_id not in self.quests:
            return False
        self._checkpoint()
        self.quests[quest_id].state = state
        self._log('quest_state_changed', {'quest_id': quest_id, 'state': state})
        return True

    def complete_quest_step(self, quest_id, step_id):
        if quest_id not in self.quests:
            return False
        quest = self.quests[quest_id]
        for step in quest.steps:
            if step.step_id == step_id and not step.completed:
                self._checkpoint()
                step.completed = True
                self._log('quest_step_completed', {'quest_id': quest_id, 'step_id': step_id})
                if all(s.completed for s in quest.steps):
                    quest.state = 'completed'
                    self._log('quest_completed', {'quest_id': quest_id})
                return True
        return False

    def set_behavior(self, behavior):
        self._checkpoint()
        self.behaviors[behavior.entity_id] = behavior
        self._log('behavior_set', {'entity_id': behavior.entity_id})
        return behavior.entity_id

    def set_weather(self, weather):
        self._checkpoint()
        self.weather = weather
        self._log('weather_changed', {'weather': weather})

    def set_player(self, eid):
        if eid in self.entities:
            self.player_entity_id = eid
            return True
        return False

    def set_audio_config(self, config):
        self._checkpoint()
        cid = f'audio_{len(self.audio_configs)}'
        self.audio_configs.append({'config_id': cid, **config})
        return cid

    def set_art_intent(self, intent):
        self._checkpoint()
        aid = f'art_{len(self.art_intents)}'
        self.art_intents.append({'intent_id': aid, **intent})
        return aid

    def tick_world(self, delta_time=None):
        self.tick += 1
        self.game_time += delta_time if delta_time is not None else 1.0 / 60.0

    def snapshot(self):
        return WorldSnapshot(
            tick=self.tick,
            entities={eid: e.to_dict() for eid, e in self.entities.items()},
            rules=[r.to_dict() for r in self.rules.values()],
            quests=[q.to_dict() for q in self.quests.values()],
            player_entity_id=self.player_entity_id,
            events=self.event_log[-50:],
            game_time=self.game_time,
            weather=self.weather,
            logs=[e['type'] for e in self.event_log[-20:]],
        )

    def to_json(self):
        return self.snapshot().to_json()

    def rollback(self):
        if not self._history:
            return False
        state = self._history.pop()
        self.entities = state['entities']
        self.rules = state['rules']
        self.quests = state['quests']
        self.behaviors = state['behaviors']
        self.player_entity_id = state['player_entity_id']
        self.weather = state['weather']
        self.game_time = state['game_time']
        self._log('rollback', {'to_tick': self.tick})
        return True

    def commit(self):
        self._history.clear()
        self._log('commit', {})

    def save_to_file(self, path):
        data = {
            'entities': {eid: e.to_dict() for eid, e in self.entities.items()},
            'rules': [r.to_dict() for r in self.rules.values()],
            'quests': [q.to_dict() for q in self.quests.values()],
            'behaviors': {eid: b.to_dict() for eid, b in self.behaviors.items()},
            'audio_configs': self.audio_configs, 'art_intents': self.art_intents,
            'player_entity_id': self.player_entity_id, 'weather': self.weather,
            'game_time': self.game_time,
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def load_from_file(self, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.entities = {eid: SemanticEntity.from_dict(ed) for eid, ed in data.get('entities', {}).items()}
        self.rules = {r['rule_id']: Rule.from_dict(r) for r in data.get('rules', [])}
        self.quests = {}
        for qd in data.get('quests', []):
            q = Quest(quest_id=qd['quest_id'], name=qd.get('name',''),
                      description=qd.get('description',''), state=qd.get('state','inactive'),
                      rewards=qd.get('rewards',[]), prerequisites=qd.get('prerequisites',[]),
                      metadata=qd.get('metadata',{}))
            q.steps = [QuestStep(**s) for s in qd.get('steps',[])]
            self.quests[q.quest_id] = q
        self.behaviors = {eid: NPCBehavior(**b) for eid, b in data.get('behaviors', {}).items()}
        self.audio_configs = data.get('audio_configs', [])
        self.art_intents = data.get('art_intents', [])
        self.player_entity_id = data.get('player_entity_id')
        self.weather = data.get('weather', 'clear')
        self.game_time = data.get('game_time', 0.0)

    @property
    def summary(self):
        types = {}
        for e in self.entities.values():
            types[e.semantic_type] = types.get(e.semantic_type, 0) + 1
        return {
            'tick': self.tick, 'game_time': f'{self.game_time:.1f}s',
            'weather': self.weather, 'entity_count': len(self.entities),
            'rule_count': len(self.rules), 'quest_count': len(self.quests),
            'player_entity': self.player_entity_id, 'entities_by_type': types,
        }


