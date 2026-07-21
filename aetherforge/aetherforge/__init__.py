'''
AetherForge - AI-Native Game Creation and Runtime System
'''
from __future__ import annotations
import json, uuid, copy
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from collections import deque as _deque
from pathlib import Path as _Path

PKG_DIR = _Path(__file__).parent
ROOT_DIR = PKG_DIR.parent
__version__ = "2.0.0"

# Re-export core types for convenience
from aetherforge.core import (
    SemanticEntity, EntityCapability, Rule, RuleTriggerType,
    Quest, QuestStep, NPCBehavior, BehaviorType,
    AudioLayer, SemanticAudioConfig, ArtIntent, WorldSnapshot,
    RelationshipType,
)
from aetherforge.core.world_model import WorldModel
from aetherforge.api.tools import EngineTools, ToolResult
