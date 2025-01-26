from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Tuple, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json

# Type definitions
SpellId = int
AuraId = int
ZoneId = int
ObjectId = int
NpcId = int
Position = Tuple[float, float]
Destination = Tuple[ObjectId, Optional[Position]]

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

@dataclass
class IdGenerator:
    EMPTY_ID: ClassVar[int] = 0
    _reserved_ids: Set[int] = field(default_factory=set)
    _assigned_ids: Deque[int] = field(default_factory=deque)

    def assign_id_range(self, start: int, stop: int) -> None:
        for id_num in range(start, stop):
            if id_num not in self._reserved_ids:
                self._assigned_ids.append(id_num)

    def new_id(self) -> int:
        assert self._assigned_ids
        if not self._assigned_ids:
            return IdGenerator.EMPTY_ID
        return self._assigned_ids.popleft()

    def reserve_id(self, reserved_id: int) -> None:
        self._reserved_ids.add(reserved_id)
        self._assigned_ids = deque(id_num for id_num in self._assigned_ids if id_num != reserved_id)

@dataclass
class Color:
    BLACK: ClassVar[Tuple[int, int, int]] = (0, 0, 0)
    WHITE: ClassVar[Tuple[int, int, int]] = (255, 255, 255)
    GREY: ClassVar[Tuple[int, int, int]] = (128, 128, 128)
    RED: ClassVar[Tuple[int, int, int]] = (255, 0, 0)
    GREEN: ClassVar[Tuple[int, int, int]] = (0, 255, 0)
    BLUE: ClassVar[Tuple[int, int, int]] = (0, 0, 255)

@dataclass
class Spell:
    spell_id: Final[SpellId]
    spawn_npc_id: NpcId = IdGenerator.EMPTY_ID
    aura_spell_id: SpellId = IdGenerator.EMPTY_ID
    cascade_spell_id: SpellId = IdGenerator.EMPTY_ID
    disabling_spell_id: SpellId = IdGenerator.EMPTY_ID
    power: float = 1.0
    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 1
    flags: SpellFlag = SpellFlag.NONE

@dataclass
class Aura:
    aura_id: Final[AuraId]
    source_id: Final[ObjectId]
    spell_id: Final[SpellId]
    target_id: Final[ObjectId]
    spell_duration: Final[float]
    spell_ticks: Final[int]
    spell_max_stacks: Final[int]
    activation_delay: float = 0.0
    time_remaining: float = 0.0
    stacks: int = 0
    tick_interval: float = 0.0
    time_since_last_tick: float = 0.0
    ticks_awaiting_processing: int = 0

@dataclass
class Npc:
    npc_id: Final[NpcId]
    hp: float = 0.0
    movement_speed: float = 1.0
    is_attackable: bool = False
    is_player: bool = False

@dataclass
class GameObj:
    obj_id: Final[ObjectId]
    position: Position
    parent_id: ObjectId = IdGenerator.EMPTY_ID
    npc_properties: Npc = field(default_factory=lambda: Npc(IdGenerator.EMPTY_ID))
    destination: Destination = field(default_factory=lambda: (IdGenerator.EMPTY_ID, None))
    hp: float = 0.0
    movement_speed: float = 1.0
    is_attackable: bool = False
    is_player: bool = False

@dataclass
class CombatEvent:
    event_id: Final[int]
    timestamp: float
    source_id: ObjectId
    spell_id: SpellId
    dest: Destination
    outcome: EventOutcome = EventOutcome.EMPTY

@dataclass
class Zone:
    zone_id: Final[ZoneId]
    player_spawn: Tuple[SpellId, Position] = field(default_factory=lambda: (IdGenerator.EMPTY_ID, (0.0, 0.0)))
    enemy_spawns: List[Tuple[SpellId, Position]] = field(default_factory=list)

@dataclass
class Ruleset:
    npcs: Dict[NpcId, Npc] = field(default_factory=dict)
    spells: Dict[SpellId, Spell] = field(default_factory=dict)
    zones: Dict[ZoneId, Zone] = field(default_factory=dict)

@dataclass
class EventLog:
    _combat_event_log: Dict[int, CombatEvent] = field(default_factory=dict)

@dataclass
class World:
    timestamp: float = 0.0
    delta_time: float = 0.0
    ruleset: Ruleset = field(default_factory=Ruleset)
    auras: Dict[AuraId, Aura] = field(default_factory=dict)
    game_objs: Dict[ObjectId, GameObj] = field(default_factory=dict)
    root_obj_id: ObjectId = IdGenerator.EMPTY_ID
    combat_event_log: EventLog = field(default_factory=EventLog)