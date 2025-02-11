from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
from typing import Any, Dict, List, Tuple, Type, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json
from src.config.color import Color


class IdGen:
    """ ID generator that provides unique IDs from a set of assigned integers. """
    EMPTY_ID = 0

    def __init__(self) -> None:
        self._reserved_ids: Set[int] = set({IdGen.EMPTY_ID})
        self._assigned_ids: Deque[int] = deque()

    @classmethod
    def create_preassigned_range(cls, id_start: int, id_stop: int) -> 'IdGen':
        id_gen = IdGen()
        id_gen.assign_id_range(id_start, id_stop)
        return id_gen

    @staticmethod
    def is_empty_id(id_num: int) -> bool:
        return id_num == IdGen.EMPTY_ID

    def assign_id_range(self, start: int, stop: int) -> None:
        for id_num in range(start, stop):
            if id_num not in self._reserved_ids:
                self._assigned_ids.append(id_num)

    def new_id(self) -> int:
        if not self._assigned_ids:
            assert self._assigned_ids, "No more IDs available."
            return IdGen.EMPTY_ID
        return self._assigned_ids.popleft()

    def reserve_id(self, reserved_id: int) -> None:
        self._reserved_ids.add(reserved_id)
        self._assigned_ids = deque(id_num for id_num in self._assigned_ids if id_num != reserved_id)


class Controls(NamedTuple):
    """ Keypresses for a given timestamp. Is used to make game objects initiate a spellcast. """
    local_timestamp: float = 0.0
    move_up: bool = False
    move_left: bool = False
    move_down: bool = False
    move_right: bool = False
    next_target: bool = False
    ability_1: bool = False
    ability_2: bool = False
    ability_3: bool = False
    ability_4: bool = False

    def is_happening_now(self, last_visit: float, now: float) -> bool:
        return self.local_timestamp > last_visit and self.local_timestamp <= now


class SpellFlag(Flag):
    """ Flags for how spells should be handled. """
    NONE = 0
    MOVE_UP = auto()
    MOVE_LEFT = auto()
    MOVE_DOWN = auto()
    MOVE_RIGHT = auto()
    SELF_CAST = auto()
    TAB_TARGET = auto()
    TELEPORT = auto()
    TRIGGER_GCD = auto()
    DAMAGE = auto()
    HEAL = auto()
    DENY_IF_CASTING = auto()
    IS_CHANNEL = auto()
    WARP_TO_POSITION = auto()
    TRY_MOVE = auto()
    FORCE_MOVE = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    AURA = auto()
    SLOT_1_ABILITY = auto()


class Spell(NamedTuple):
    """ An action that can be performed by a game object. """
    spell_id: int = IdGen.EMPTY_ID
    alias_id: int = IdGen.EMPTY_ID
    aura_effect_id: int = IdGen.EMPTY_ID

    power: float = 1.0
    variance: float = 0.0

    #self.cost: float = 0 #not yet implemented
    #self.range_limit: float = 0 #not yet implemented
    #self.gcd_mod: float = 0.0 #not yet implemented
    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 1

    flags: SpellFlag = SpellFlag.NONE

    spell_sequence: Optional[Tuple[int, ...]] = None
    spawned_obj: Optional['GameObj'] = None
    controls: Optional[Tuple[Controls, ...]] = None


class Aura(NamedTuple):
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    target_id: int = IdGen.EMPTY_ID
    start_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    is_debuff: bool = False
    is_hidden: bool = False

    @property
    def aura_id(self) -> Tuple[int, int, int]:
        return self.source_id, self.spell_id, self.target_id

    @property
    def tick_interval(self) -> float:
        if self.ticks == 0 or self.duration == 0:
            return float('inf')
        return self.duration / self.ticks

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

    @classmethod
    def create_from_spell(cls, timestamp: float, source_id: int, spell: Spell, target_id: int) -> 'Aura':
        return Aura(
            source_id=source_id,
            spell_id=spell.aura_effect_id,
            target_id=target_id,
            start_time=timestamp,
            duration=spell.duration,
            ticks=spell.ticks,
        )

    def is_expired(self, current_time: float) -> bool:
        return current_time > self.end_time

    def ticks_elapsed(self, current_time: float) -> int:
        return max(0, math.floor((current_time - self.start_time) / self.tick_interval))

    def ticks_remaining(self, current_time: float) -> int:
        return max(0, self.ticks - self.ticks_elapsed(current_time))

    def next_tick(self, current_time: float) -> float:
        if self.ticks_remaining(current_time) == 0:
            return float('inf')
        return self.start_time + ((self.ticks_elapsed(current_time) + 1) * self.tick_interval)

    def has_tick_this_frame(self, frame_start: float, frame_end: float) -> bool:
        """ Ticks happen every tick_interval seconds, excluding t=start, including t=end. """
        start_ticks = self.ticks_elapsed(max(frame_start, self.start_time))
        end_ticks = self.ticks_elapsed(min(frame_end, self.end_time))
        return end_ticks > start_ticks

    def get_timestamp_for_ticks_this_frame(self, frame_start: float, frame_end: float) -> Tuple[float, ...]:
        start_ticks = self.ticks_elapsed(max(frame_start, self.start_time))
        end_ticks = self.ticks_elapsed(min(frame_end, self.end_time))
        return tuple(self.start_time + (tick_number * self.tick_interval) for tick_number in range(start_ticks + 1, end_ticks + 1))


class EventTrigger(Enum):
    EMPTY = 0
    CONTROLS = 1
    CAST_FINISH = 2
    AURA_TICK = 3


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = 1
    FAILED = 2
    MISSED = 3


class CombatEvent(NamedTuple):
    event_id: int = IdGen.EMPTY_ID
    base_event: int = IdGen.EMPTY_ID
    timestamp: float = 0.0
    source: int = IdGen.EMPTY_ID
    spell: int = IdGen.EMPTY_ID
    target: int = IdGen.EMPTY_ID
    is_aura_tick: bool = False
    outcome: EventOutcome = EventOutcome.EMPTY

    @classmethod
    def create_from_aura_tick(cls, event_id: int, timestamp: float, aura: Aura) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=aura.source_id,
            spell=aura.spell_id,
            target=aura.target_id,
            is_aura_tick=True,
        )

    @classmethod
    def create_from_controls(cls, event_id: int, timestamp: float, source_id: int, spell_id: int, target_id: int) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=source_id,
            spell=spell_id,
            target=target_id,
        )

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] (obj_{self.source:04d} uses spell_{self.spell:04d} on obj_{self.target:04d}.)"

    @property
    def is_aoe(self) -> bool:
        return False #fix later

    @property
    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.target)

    def new_target(self, new_target: int) -> 'CombatEvent':
        return self._replace(target=new_target)

    def finalize_outcome(self, new_outcome: EventOutcome) -> 'CombatEvent':
        return self._replace(outcome=new_outcome)

    def continue_spell_sequence(self, new_event_id: int, new_spell_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, spell=new_spell_id)

    def also_target(self, new_event_id: int, new_target_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, target=new_target_id)


class GameObjStatus(Enum):
    """ Flags for various status effects of game objects. """
    NONE = 0
    CASTING = auto()
    CHANNELING = auto()
    CROWD_CONTROLLED = auto()
    BANISHED = auto()


@dataclass
class GameObj:
    """ Combat units. Controlled by the player or NPCs. """
    obj_id: int = IdGen.EMPTY_ID
    parent_id: int = IdGen.EMPTY_ID
    spawned_from_spell: Final[int] = IdGen.EMPTY_ID

    # Appearance
    color: Tuple[int, int, int] = Color.WHITE

    # Status effects
    statuses: GameObjStatus = GameObjStatus.NONE

    # Targeting
    is_allied: bool = False
    current_target: int = IdGen.EMPTY_ID
    selected_spell: int = IdGen.EMPTY_ID

    # Combat stats
    hp: float = 0.0
    movement_speed: float = 1.0
    is_attackable: bool = False
    is_player: bool = False
    gcd: float = 1.0

    # Positional data
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0

    # Ability slots
    move_up_id: int = IdGen.EMPTY_ID
    move_left_id: int = IdGen.EMPTY_ID
    move_down_id: int = IdGen.EMPTY_ID
    move_right_id: int = IdGen.EMPTY_ID
    next_target: int = IdGen.EMPTY_ID
    ability_1_id: int = IdGen.EMPTY_ID
    ability_2_id: int = IdGen.EMPTY_ID
    ability_3_id: int = IdGen.EMPTY_ID
    ability_4_id: int = IdGen.EMPTY_ID

    # Cooldown timestamps
    spawn_timestamp: float = 0.0
    gcd_start: float = 0.0
    ability_1_cd_start: float = 0.0
    ability_2_cd_start: float = 0.0
    ability_3_cd_start: float = 0.0
    ability_4_cd_start: float = 0.0

    @property
    def size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.hp))

    @property
    def spell_modifier(self) -> float:
        #calculation not yet implemented
        return 1.0

    @property
    def gcd_progress(self) -> float:
        return min(1.0, (0 - self.gcd_start) / self.gcd)

    @classmethod
    def create_from_template(cls, unique_obj_id: int, parent_id: int, other: 'GameObj') -> 'GameObj':
        new_obj: GameObj = other.copy()
        new_obj.obj_id = unique_obj_id
        new_obj.parent_id = parent_id
        return new_obj

    def copy(self) -> 'GameObj':
        return copy(self)

    def teleport_to(self, new_x: float, new_y: float) -> None:
        self.x = new_x
        self.y = new_y

    def move_in_direction(self, x: float, y: float, move_speed: float, delta_t: float) -> None:
        self.x += x * move_speed * delta_t
        self.y += y * move_speed * delta_t

    def switch_target(self, new_target: int) -> None:
        self.current_target = new_target

    def suffer_damage(self, spell_power: float) -> None:
        self.hp -= spell_power

    def restore_health(self, spell_power: float) -> None:
        self.hp += spell_power

    def time_since_spawn(self, current_time: float) -> float:
        return current_time - self.spawn_timestamp

    def convert_to_events(self, id_gen: IdGen, timestamp: float, controls: Controls) -> List[CombatEvent]:
        spell_ids: List[int] = []
        spell_ids += [self.move_up_id] if controls.move_up else []
        spell_ids += [self.move_left_id] if controls.move_left else []
        spell_ids += [self.move_down_id] if controls.move_down else []
        spell_ids += [self.move_right_id] if controls.move_right else []
        spell_ids += [self.next_target] if controls.next_target else []
        spell_ids += [self.ability_1_id] if controls.ability_1 else []
        spell_ids += [self.ability_2_id] if controls.ability_2 else []
        spell_ids += [self.ability_3_id] if controls.ability_3 else []
        spell_ids += [self.ability_4_id] if controls.ability_4 else []
        assert IdGen.EMPTY_ID not in spell_ids, f"Controls {controls} resulted in an empty spell being cast."
        events: List[CombatEvent] = []
        for spell_id in spell_ids:
            events.append(CombatEvent.create_from_controls(id_gen.new_id(), timestamp, self.obj_id, spell_id, self.current_target))
        return events