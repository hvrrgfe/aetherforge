"""Art Director - visual review and style consistency checking.

READ-ONLY role. Reviews scene composition, visual consistency,
and generates style reports.
"""
import uuid, time
from typing import Optional, Dict, List, Any
from aetherforge.agents.roles.explorer import BaseAgentRole

class ArtDirector(BaseAgentRole):
    """Visual reviewer that checks scene composition and style."""

    def __init__(self, gateway, evidence_store=None, state_manager=None):
        super().__init__(gateway, evidence_store, state_manager)
        self.role = "art_director"
        self._findings = []

    def review_scene(self, world_model=None, screenshot_url: str = "") -> Dict:
        """Review scene for visual consistency and composition."""
        self._findings = []
        entities = getattr(world_model, 'entities', {}) if world_model else {}
        visual_issues = self._check_visual_consistency(entities)
        composition_issues = self._check_composition(entities)

        self._findings.extend(visual_issues)
        self._findings.extend(composition_issues)

        blocking = [f for f in self._findings if f.get("blocking")]
        return {
            "total_findings": len(self._findings),
            "blocking": len(blocking),
            "findings": self._findings,
        }

    def _check_visual_consistency(self, entities: Dict) -> List[Dict]:
        """Check visual properties of entities.""" 
        issues = []
        for eid, ent in entities.items():
            visual = getattr(ent, 'visual', None) or {}
            if isinstance(visual, dict) and not visual.get("color") and not visual.get("mesh"):
                issues.append({
                    "severity": "low",
                    "type": "missing_visual",
                    "description": f"Entity {eid} has no visual properties",
                    "entity_id": eid,
                })
            name = getattr(ent, 'name', '') if not isinstance(ent, dict) else ent.get('name', '')
            sem_type = getattr(ent, 'semantic_type', '') if not isinstance(ent, dict) else ent.get('semantic_type', '')
            if sem_type in ("npc", "character") and not name:
                issues.append({
                    "severity": "medium",
                    "type": "unnamed_character",
                    "description": f"Character entity {eid} has no name",
                    "entity_id": eid,
                })
        return issues

    def _check_composition(self, entities: Dict) -> List[Dict]:
        """Check scene composition."""
        issues = []
        npcs = []
        items = []
        for eid, ent in entities.items():
            sem_type = getattr(ent, 'semantic_type', '') if not isinstance(ent, dict) else ent.get('semantic_type', '')
            if sem_type in ("npc", "character"):
                npcs.append(eid)
            elif sem_type in ("item", "object"):
                items.append(eid)

        if len(npcs) > 0 and len(items) == 0:
            issues.append({
                "severity": "low",
                "type": "no_interactive_items",
                "description": f"Scene has {len(npcs)} NPCs but no interactive items",
                "blocking": False,
            })
        if len(entities) == 0:
            issues.append({
                "severity": "high",
                "type": "empty_scene",
                "description": "Scene has no entities",
                "blocking": True,
            })
        return issues

    def generate_style_report(self, world_model=None) -> Dict:
        """Generate a style consistency report."""
        entities = getattr(world_model, 'entities', {}) if world_model else {}
        types = {}
        for eid, ent in entities.items():
            sem_type = getattr(ent, 'semantic_type', '') if not isinstance(ent, dict) else ent.get('semantic_type', '')
            types[sem_type] = types.get(sem_type, 0) + 1
        return {
            "entity_type_distribution": types,
            "total_entities": len(entities),
            "findings": len(self._findings),
        }

    def to_dict(self) -> Dict:
        return {"role": self.role, "findings": len(self._findings)}