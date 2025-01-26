from dataclasses import dataclass, asdict
import json
import math
from typing import Dict, Any, List, TypedDict, Tuple, Optional, FrozenSet, Literal
from types import MappingProxyType
from enum import Flag, Enum, auto

# Constants and Enums
class Color(TypedDict):
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    GREY: Tuple[int, int, int] = (128, 128, 128)
    RED: Tuple[int, int, int] = (255, 0, 0)
    GREEN: Tuple[int, int, int] = (0, 255, 0)
    BLUE: Tuple[int, int, int] = (0, 0, 255)

class SpellFlag(Flag):
    NONE = 0
    MOVEMENT = auto()
    TELEPORT = auto()
    FIND_TARGET = auto()
    GCD = auto()
    DAMAGE = auto()
    HEAL = auto()
    STOP_CAST = auto()
    IS_CHANNEL = auto()
    WARP_TO_POSITION = auto()
    TRY_MOVE = auto()
    FORCE_MOVE = auto()

class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = 1
    FAILED = 2
    MISSED = 3

# Type definitions
SpellId = int
AuraId = int
ZoneId = int
ObjectId = int
NpcId = int
Position = Tuple[float, float]
Destination = Tuple[ObjectId, Optional[Position]]

# Immutable Configuration Classes
@dataclass(frozen=True)
class Spell:
    spell_id: SpellId
    power: float = 1.0
    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 0
    flags: SpellFlag = SpellFlag.NONE
    spawn_npc_id: ObjectId = 0
    aura_spell_id: SpellId = 0
    cascade_spell_id: SpellId = 0
    disabling_spell_id: SpellId = 0

@dataclass(frozen=True)
class Npc:
    npc_id: NpcId
    hp: float
    movement_speed: float = 1.0
    is_attackable: bool = False
    is_player: bool = False

@dataclass(frozen=True)
class Zone:
    zone_id: ZoneId
    player_spawn: Tuple[NpcId, Position]
    enemy_spawns: Tuple[Tuple[NpcId, Position], ...]

# Mutable State Classes
class Aura:
    def __init__(self, aura_id: AuraId, source_id: ObjectId, spell: Spell, target_id: ObjectId):
        self.aura_id = aura_id
        self.source_id = source_id
        self.spell_id = spell.spell_id
        self.spell_duration = spell.duration
        self.spell_ticks = spell.ticks
        self.spell_max_stacks = spell.max_stacks
        self.target_id = target_id

        self.activation_delay = 0.0
        self.time_remaining = 0.0
        self.stacks = 0
        self.tick_interval = 0.0
        self.time_since_last_tick = 0.0
        self.ticks_awaiting_processing = 0

    def is_active(self) -> bool:
        return self.time_remaining > 0.0 and self.activation_delay <= 0.0

    def apply_stack(self) -> None:
        new_time_remaining = self.spell_duration
        if self.stacks == self.spell_max_stacks:
            PANDEMIC_COEFFICIENT = 0.3
            pandemic_window = self.spell_duration * PANDEMIC_COEFFICIENT
            new_time_remaining += min(pandemic_window, self.time_remaining)
        self.stacks = min(self.stacks + 1, self.spell_max_stacks)
        self.time_remaining = new_time_remaining
        self.tick_interval = self.time_remaining / max(1, self.spell_ticks)

    def update_timers(self, delta_time: float) -> None:
        self.activation_delay -= delta_time
        if self.activation_delay > 0.0:
            return
        if self.spell_ticks > 0:
            self.time_since_last_tick += delta_time
            if self.time_since_last_tick >= self.tick_interval:
                self.time_since_last_tick -= self.tick_interval
                self.ticks_awaiting_processing += self.stacks
        self.time_remaining -= delta_time
        if self.time_remaining <= 0.0:
            self.time_remaining = 0.0
            self.stacks = 0
            self.tick_interval = 0.0
            self.time_since_last_tick = 0.0

class GameObject:
    def __init__(self, obj_id: ObjectId, position: Position):
        self.obj_id = obj_id
        self.parent_id = 0  # EMPTY_ID
        self.position = position
        self.destination = None
        self.hp = 0.0
        self.movement_speed = 1.0
        self.is_attackable = False
        self.is_player = False
        self._npc_properties: Optional[Npc] = None

    def load_npc_data(self, npc: Npc) -> None:
        self._npc_properties = npc
        self.hp = npc.hp
        self.is_attackable = npc.is_attackable
        self.is_player = npc.is_player

    def get_size(self) -> float:
        return 0.01 + math.sqrt(0.0001 * abs(self.hp))

    def teleport_to(self, new_position: Position) -> None:
        self.position = new_position

    def suffer_damage(self, spell_power: float) -> None:
        self.hp -= spell_power

    def restore_health(self, spell_power: float) -> None:
        self.hp += spell_power

@dataclass(frozen=True)
class GameConfig:
    data: Dict[str, Any]

    @classmethod
    def create(cls, data: dict) -> 'GameConfig':
        return cls({
            'spells': data.get('spells', {}),
            'npcs': data.get('npcs', {}),
            'zones': data.get('zones', {})
        })

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'GameConfig':
        return cls.create(json.loads(json_str))

    def get_spell(self, spell_id: int) -> dict:
        return self.data['spells'].get(str(spell_id), {})

    def get_npc(self, npc_id: int) -> dict:
        return self.data['npcs'].get(str(npc_id), {})

@dataclass(frozen=True)
class GameState:
    data: Dict[str, Any]

    @classmethod
    def create(cls, data: dict) -> 'GameState':
        return cls({
            'timestamp': data.get('timestamp', 0.0),
            'delta_time': data.get('delta_time', 0.0),
            'game_objects': data.get('game_objects', {}),
            'auras': data.get('auras', {}),
            'combat_log': data.get('combat_log', []),
            'root_obj_id': data.get('root_obj_id', 0)
        })

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'GameState':
        return cls.create(json.loads(json_str))

    def get_object(self, obj_id: int) -> dict:
        return self.data['game_objects'].get(str(obj_id), {})

    def get_aura(self, aura_id: int) -> dict:
        return self.data['auras'].get(str(aura_id), {})

class FullGameState:
    data: Dict[str, Any]

    @classmethod
    def create(cls, data: dict) -> 'FullGameState':
        return cls(data)

    # Deserialize from JSON string
    @classmethod
    def from_json(cls, json_str: str) -> 'FullGameState':
        data = json.loads(json_str)
        return cls.create(data)

    # Serialize to JSON string
    def to_json(self) -> str:
        return json.dumps(asdict(self))