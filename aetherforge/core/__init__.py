'''
AetherForge - AI-Native Game Creation and Runtime System
Core types and semantic world model.
'''
from __future__ import annotations
import json, uuid, copy
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

class EntityCapability(str, Enum):
    OPEN = 'open'
    CLOSE = 'close'
    LOCK = 'lock'
    UNLOCK = 'unlock'
    PICK_UP = 'pick_up'
    DROP = 'drop'
    USE = 'use'
    INSPECT = 'inspect'
    TALK = 'talk'
    MOVE = 'move'
    ATTACK = 'attack'
    INTERACT = 'interact'

class RelationshipType(str, Enum):
    CONTAINS = 'contains'
    BLOCKS = 'blocks'
    LEADS_TO = 'leads_to'
    REQUIRES = 'requires'
    PART_OF = 'part_of'
    NEAR = 'near'
    INSIDE = 'inside'
    ON = 'on'
    GUARDS = 'guards'
    OWNS = 'owns'

class RuleTriggerType(str, Enum):
    INTERACTION = 'interaction'
    PROXIMITY = 'proximity'
    STATE_CHANGE = 'state_change'
    TIME = 'time'
    QUEST_EVENT = 'quest_event'
    CUSTOM = 'custom'

class BehaviorType(str, Enum):
    GOAL_ORIENTED = 'goal_oriented'
    STATE_MACHINE = 'state_machine'
    SCRIPTED = 'scripted'
    WANDER = 'wander'
    PATROL = 'patrol'
    FLEE = 'flee'


@dataclass
class SemanticEntity:
    entity_id: str = field(default_factory=lambda: f'ent_{uuid.uuid4().hex[:8]}')
    semantic_type: str = 'generic'
    name: str = ''
    description: str = ''
    capabilities: list = field(default_factory=list)
    requires: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)
    relationships: list = field(default_factory=list)
    editable_properties: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    position: dict = field(default_factory=lambda: {'x': 0.0, 'y': 0.0})
    size: dict = field(default_factory=lambda: {'width': 32.0, 'height': 32.0})
    visual: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    # AI summary fields (WP5)
    ai_summary: str = ''
    state_summary: str = ''
    relations_summary: list = field(default_factory=list)

    def to_dict(self):
        return {'entity_id': self.entity_id, 'semantic_type': self.semantic_type,
                'name': self.name, 'description': self.description,
                'capabilities': self.capabilities, 'requires': self.requires,
                'state': self.state, 'relationships': self.relationships,
                'editable_properties': self.editable_properties, 'tags': self.tags,
                'position': self.position, 'size': self.size, 'visual': self.visual,
                'metadata': self.metadata,
                'ai_summary': self.ai_summary, 'state_summary': self.state_summary,
                'relations_summary': self.relations_summary}

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def auto_summarize(self) -> None:
        """Auto-generate AI summary fields from existing data."""
        parts = []
        if self.name:
            parts.append(self.name)
        if self.semantic_type:
            parts.append(f"({self.semantic_type})")
        if self.description:
            parts.append(f"- {self.description[:100]}")
        if self.capabilities:
            parts.append(f"Capabilities: {', '.join(self.capabilities[:5])}")
        self.ai_summary = ' '.join(parts)

        # State summary
        if self.state:
            state_items = [f"{k}={v}" for k, v in list(self.state.items())[:5]]
            self.state_summary = ', '.join(state_items)
        else:
            self.state_summary = 'default state'

        # Relations summary
        self.relations_summary = []
        for rel in self.relationships[:10]:
            if isinstance(rel, dict):
                t = rel.get('type', 'relates_to')
                target = rel.get('target_id', rel.get('target', 'unknown'))
                self.relations_summary.append(f"{t} {target}")
            elif isinstance(rel, str):
                self.relations_summary.append(rel)


@dataclass
class Rule:
    rule_id: str = field(default_factory=lambda: f'rule_{uuid.uuid4().hex[:8]}')
    when: list = field(default_factory=list)
    then: list = field(default_factory=list)
    else_then: list = field(default_factory=list)
    trigger_type: RuleTriggerType = RuleTriggerType.INTERACTION
    cooldown: float = 0.0
    priority: int = 0
    enabled: bool = True
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d['trigger_type'] = self.trigger_type.value
        d['else'] = d.pop('else_then', [])
        return d

    @classmethod
    def from_dict(cls, d):
        if 'else' in d:
            d['else_then'] = d.pop('else')
        if isinstance(d.get('trigger_type'), str):
            d['trigger_type'] = RuleTriggerType(d['trigger_type'])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class QuestStep:
    step_id: str = ''
    description: str = ''
    condition: str = ''
    completed: bool = False

@dataclass
class Quest:
    quest_id: str = field(default_factory=lambda: f'q_{uuid.uuid4().hex[:8]}')
    name: str = ''
    description: str = ''
    steps: list = field(default_factory=list)
    state: str = 'inactive'
    rewards: list = field(default_factory=list)
    prerequisites: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {'quest_id': self.quest_id, 'name': self.name,
                'description': self.description, 'state': self.state,
                'steps': [{'step_id': s.step_id, 'description': s.description,
                           'condition': s.condition, 'completed': s.completed}
                          for s in self.steps],
                'rewards': self.rewards, 'prerequisites': self.prerequisites,
                'metadata': self.metadata}

@dataclass
class NPCBehavior:
    entity_id: str = ''
    behavior_type: BehaviorType = BehaviorType.GOAL_ORIENTED
    goals: list = field(default_factory=list)
    states: list = field(default_factory=list)
    fallback_action: str = 'idle'
    speed: float = 60.0
    perception_range: float = 200.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d['behavior_type'] = self.behavior_type.value
        return d

@dataclass
class AudioLayer:
    name: str = ''
    file: str = ''
    volume: float = 0.5
    loop: bool = True

@dataclass
class SemanticAudioConfig:
    intent: str = ''
    mood: list = field(default_factory=list)
    intensity: dict = field(default_factory=dict)
    layers: list = field(default_factory=list)

    def to_dict(self):
        return {'intent': self.intent, 'mood': self.mood,
                'intensity': self.intensity,
                'layers': [{'name': l.name, 'file': l.file,
                            'volume': l.volume, 'loop': l.loop}
                           for l in self.layers]}

@dataclass
class ArtIntent:
    intent: str = ''
    style: str = ''
    function: str = ''
    interaction: str = ''
    performance_budget: dict = field(default_factory=dict)

    def to_dict(self):
        return {'intent': self.intent, 'style': self.style,
                'function': self.function, 'interaction': self.interaction,
                'performance_budget': self.performance_budget}


@dataclass
class WorldSnapshot:
    tick: int = 0
    entities: dict = field(default_factory=dict)
    rules: list = field(default_factory=list)
    quests: list = field(default_factory=list)
    player_entity_id: str = None
    active_dialogues: list = field(default_factory=list)
    events: list = field(default_factory=list)
    game_time: float = 0.0
    weather: str = 'clear'
    camera: dict = field(default_factory=lambda: {'x': 0.0, 'y': 0.0})
    logs: list = field(default_factory=list)
    performance: dict = field(default_factory=dict)

    def to_dict(self):
        return {'tick': self.tick, 'entities': self.entities,
                'rules': self.rules, 'quests': self.quests,
                'player_entity_id': self.player_entity_id,
                'active_dialogues': self.active_dialogues,
                'events': self.events, 'game_time': self.game_time,
                'weather': self.weather, 'camera': self.camera,
                'logs': self.logs, 'performance': self.performance}

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)