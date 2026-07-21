"""World Model - core state management for the game world."""
import json, uuid, copy, time, os
from pathlib import Path
from typing import Optional, Dict, List, Any
from aetherforge.core import SemanticEntity

class WorldModel:
    """Represents the complete game world state."""

    def __init__(self):
        self.entities: Dict[str, SemanticEntity] = {}
        self.rules: Dict[str, Any] = {}
        self.quests: Dict[str, Any] = {}
        self.behaviors: Dict[str, Any] = {}
        self.audio_configs = []
        self.art_intents = []
        self.player_entity_id = None
        self.tick = 0
        self.game_time = 0.0
        self.weather = "clear"
        self.camera = {"x": 0.0, "y": 0.0}
        self.revision = 0
        self._history = []
        self._logs = []
        self._max_history = 50

    def _checkpoint(self):
        """Save state for rollback."""
        state = {
            "entities": {eid: copy.deepcopy(e) for eid, e in self.entities.items()},
            "rules": copy.deepcopy(self.rules),
            "quests": copy.deepcopy(self.quests),
            "behaviors": copy.deepcopy(self.behaviors),
            "player_entity_id": self.player_entity_id,
            "tick": self.tick,
            "game_time": self.game_time,
            "weather": self.weather,
            "camera": dict(self.camera),
        }
        self._history.append(state)
        while len(self._history) > self._max_history:
            self._history.pop(0)

    def _log(self, event_type, data):
        self._logs.append({
            "tick": self.tick, "time": self.game_time,
            "event": event_type, "data": data,
        })
        if len(self._logs) > 1000:
            self._logs = self._logs[-500:]

    def create_entity(self, entity):
        self._checkpoint()
        self.revision += 1
        self.entities[entity.entity_id] = entity
        self._log("entity_created", {"entity_id": entity.entity_id, "name": entity.name})
        return entity.entity_id

    def modify_entity(self, entity_id, changes):
        if entity_id not in self.entities:
            return False
        self._checkpoint()
        self.revision += 1
        ent = self.entities[entity_id]
        for key, val in changes.items():
            if hasattr(ent, key):
                if key == "state" and isinstance(val, dict):
                    ent.state.update(val)
                else:
                    setattr(ent, key, val)
        self._log("entity_modified", {"entity_id": entity_id, "changes": changes})
        return True

    def remove_entity(self, entity_id):
        if entity_id not in self.entities:
            return False
        self._checkpoint()
        self.revision += 1
        if self.player_entity_id == entity_id:
            self.player_entity_id = None
        del self.entities[entity_id]
        self.behaviors.pop(entity_id, None)
        self._log("entity_removed", {"entity_id": entity_id})
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
                if key == "state" and isinstance(val, dict):
                    ent.state.update(val)
                else:
                    setattr(ent, key, val)
        self.revision += 1
        return True

    def quick_remove_entity(self, entity_id):
        if entity_id not in self.entities:
            return False
        if self.player_entity_id == entity_id:
            self.player_entity_id = None
        del self.entities[entity_id]
        self.behaviors.pop(entity_id, None)
        self.revision += 1
        return True

    def quick_create_entity(self, entity):
        """High-frequency create: skip checkpoint deepcopy."""
        self.entities[entity.entity_id] = entity
        self.revision += 1
        return entity.entity_id

    def find_entities(self, **filters):
        """Find entities by exact field match or semantic query.

        Supports: semantic_type, tag, name_contains, desc_contains,
        capability, ai_search for ai_summary matching.
        """
        results = list(self.entities.values())
        ai_search = filters.pop("ai_search", "")
        for key, val in filters.items():
            if key == "semantic_type":
                results = [e for e in results if e.semantic_type == val]
            elif key == "tag":
                results = [e for e in results if val in e.tags]
            elif key == "name_contains":
                results = [e for e in results if val.lower() in e.name.lower()]
            elif key == "desc_contains":
                results = [e for e in results if val.lower() in e.description.lower()]
            elif key == "capability":
                results = [e for e in results if val in e.capabilities]
        if ai_search:
            q = ai_search.lower()
            results = [e for e in results if
                       q in e.ai_summary.lower() or
                       q in e.name.lower() or
                       q in e.description.lower() or
                       q in e.state_summary.lower() or
                       q in str(e.relations_summary).lower()]
        return results

    def auto_generate_summaries(self) -> int:
        """Auto-generate ai_summary, state_summary, relations_summary for all entities."""
        count = 0
        for e in self.entities.values():
            e.auto_summarize()
            count += 1
        return count

    def set_player(self, eid):
        if eid in self.entities:
            self.player_entity_id = eid
            return True
        return False

    def set_audio_config(self, config):
        self._checkpoint()
        cid = f"audio_{len(self.audio_configs)}"
        self.audio_configs.append(config)
        self._log("audio_config_set", {"config_id": cid})

    def set_art_intent(self, intent):
        self._checkpoint()
        self.art_intents.append(intent)
        self._log("art_intent_set", {"intent": intent})

    def tick_world(self):
        self.tick += 1
        self.game_time += 0.016

    def snapshot(self):
        """Return a serializable world snapshot."""
        return {
            "tick": self.tick, "game_time": self.game_time, "weather": self.weather,
            "revision": self.revision,
            "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
            "rules": [r.to_dict() for r in self.rules.values()],
            "quests": [q.to_dict() for q in self.quests.values()],
            "player_entity_id": self.player_entity_id,
        }

    @property
    def summary(self):
        types = {}
        for e in self.entities.values():
            types[e.semantic_type] = types.get(e.semantic_type, 0) + 1
        return {
            "tick": self.tick, "game_time": f"{self.game_time:.1f}s",
            "weather": self.weather, "entity_count": len(self.entities),
            "revision": self.revision,
            "rule_count": len(self.rules), "quest_count": len(self.quests),
            "player_entity": self.player_entity_id, "entities_by_type": types,
        }

    def rollback(self):
        if not self._history:
            return False
        state = self._history.pop()
        self.entities = state["entities"]
        self.rules = state["rules"]
        self.quests = state["quests"]
        self.behaviors = state["behaviors"]
        self.player_entity_id = state["player_entity_id"]
        self.tick = state["tick"]
        self.game_time = state["game_time"]
        self.weather = state["weather"]
        self.camera = state["camera"]
        return True

    def commit(self):
        """Apply and finalize current state."""
        self._history.clear()

    def add_rule(self, rule):
        self._checkpoint()
        self.revision += 1
        self.rules[rule.rule_id] = rule
        self._log("rule_added", {"rule_id": rule.rule_id})
        return rule.rule_id

    def remove_rule(self, rule_id):
        if rule_id in self.rules:
            self._checkpoint()
            self.revision += 1
            del self.rules[rule_id]
            self._log("rule_removed", {"rule_id": rule_id})
            return True
        return False

    def find_rules_by_trigger(self, trigger_type):
        return [r for r in self.rules.values()
                if r.trigger_type == trigger_type]

    def create_quest(self, quest):
        self.quests[quest.quest_id] = quest
        self._log("quest_created", {"quest_id": quest.quest_id})
        return quest.quest_id

    def update_quest_state(self, quest_id, new_state):
        if quest_id in self.quests:
            self.quests[quest_id].state = new_state
            self._log("quest_state_changed", {"quest_id": quest_id, "state": new_state})

    def complete_quest_step(self, quest_id, step_id):
        if quest_id in self.quests:
            for step in self.quests[quest_id].steps:
                if step.step_id == step_id:
                    step.completed = True
                    self._log("quest_step_completed", {"quest_id": quest_id, "step_id": step_id})
                    return True
        return False

    def set_behavior(self, entity_id, behavior_data):
        self._checkpoint()
        self.revision += 1
        self.behaviors[entity_id] = behavior_data
        self._log("behavior_set", {"entity_id": entity_id})

    def set_weather(self, weather):
        self.weather = weather
        self._log("weather_set", {"weather": weather})

    def to_json(self):
        return json.dumps(self.snapshot(), indent=2, ensure_ascii=False)

    def save_to_file(self, path):
        Path(path).write_text(self.to_json(), encoding="utf-8")

    def load_from_file(self, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.entities = {eid: SemanticEntity.from_dict(ed) for eid, ed in data.get("entities", {}).items()}
        self.rules = {r["rule_id"]: Rule.from_dict(r) for r in data.get("rules", [])}
        self.quests = {}
        self.behaviors = {}
        self.player_entity_id = data.get("player_entity_id")
        self.tick = data.get("tick", 0)
        self.game_time = data.get("game_time", 0.0)
        self.weather = data.get("weather", "clear")
        self.camera = data.get("camera", {"x": 0.0, "y": 0.0})
        self.revision = 0
        self._history = []
        # Auto-generate summaries on load
        self.auto_generate_summaries()
