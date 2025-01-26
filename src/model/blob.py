from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Tuple, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json


class Color:
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    GREY: Tuple[int, int, int] = (128, 128, 128)
    RED: Tuple[int, int, int] = (255, 0, 0)
    GREEN: Tuple[int, int, int] = (0, 255, 0)
    BLUE: Tuple[int, int, int] = (0, 0, 255)


class IdGenerator:
    EMPTY_ID = 0

    def __init__(self, assigned_id_start: int, assigned_id_stop: int) -> None:
        self._reserved_ids: Set[int] = set()
        self._assigned_ids: Deque[int] = deque()
        self.assign_id_range(assigned_id_start, assigned_id_stop)

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


class Spell(NamedTuple):
    spell_id: int = IdGenerator.EMPTY_ID
    spawn_npc_id: int = IdGenerator.EMPTY_ID
    aura_spell_id: int = IdGenerator.EMPTY_ID
    cascade_spell_id: int = IdGenerator.EMPTY_ID
    disabling_spell_id: int = IdGenerator.EMPTY_ID

    power: float = 1.0
    variance: float = 0 #not yet implemeted
    cost: float = 0 #not yet implemented
    range_limit: float = 0 #not yet implemented
    gcd_mod: float = 0.0 #not yet implemented

    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 1

    flags: SpellFlag = SpellFlag.NONE


class Destination(NamedTuple):
    target_obj_id: int = IdGenerator.EMPTY_ID
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    is_: bool = False
    max_range: float = 0.0
    min_range: float = 0.0
    is_cone_shaped: bool = False
    is_rectangle: bool = False
    angle_width: float = 0.0


class Aura(NamedTuple):
    source_id: int = IdGenerator.EMPTY_ID
    spell_id: int = IdGenerator.EMPTY_ID
    target_id: int = IdGenerator.EMPTY_ID
    start: float = 0.0
    end: float = 0.0
    tick_interval: float = float('inf')
    stacks: int = 0

    def apply_aura(self, source_id: int, spell: Spell, target_id: int, timestamp: float) -> None:
        self.source_id = source_id
        self.spell_id = spell.spell_id
        self.target_id = target_id
        self.start = timestamp
        self.end = timestamp + spell.duration
        self.tick_interval = float('inf') if spell.ticks == 0 else spell.duration / spell.ticks

    def has_tick_in_interval(self, previous_timestamp: float, current_timestamp) -> bool:
        """
        Aura ticks happen every tick_interval seconds after application.
        Example timing: If aura starts at 10.0 with tick_interval=2.5,
        ticks occur at 12.5, 15.0, 17.5, 20.0. Example:
            >>> aura = Aura(start=10.0, end=20.0, tick_interval=2.5)
            >>> aura.has_tick_in_interval(12.0, 13.0)  # True (tick at 12.5)
            >>> aura.has_tick_in_interval(13.0, 14.0)  # False (no tick)
        """
        if previous_timestamp >= self.end or current_timestamp <= self.start:
            return False
        tick_interval = max(0.1, self.tick_interval) #minimum tick interval is 0.1 seconds
        ticks_elapsed = max(0, (previous_timestamp - self.start) / tick_interval)
        next_tick = self.start + (math.ceil(ticks_elapsed) * tick_interval)
        return (previous_timestamp < next_tick <= current_timestamp) and (next_tick <= self.end)


class CombatInput(NamedTuple):
    timestamp: float = -1.0
    move_up: bool = False
    move_left: bool = False
    move_down: bool = False
    move_right: bool = False
    ability_1: bool = False
    ability_2: bool = False
    ability_3: bool = False
    ability_4: bool = False


@dataclass
class CombatObj:
    obj_id: int = IdGenerator.EMPTY_ID
    target_obj_id: int = IdGenerator.EMPTY_ID
    spec_id: int = IdGenerator.EMPTY_ID

    position_x: float = 0.0
    position_y: float = 0.0
    rotation: float = 0.0
    hp: float = 0.0
    movement_speed: float = 1.0
    is_attackable: bool = True
    is_enemy: bool = True

    inputs: Dict[float, CombatInput] = {}
    auras: Dict[int, Aura] = {}
    ability_1_id: int = IdGenerator.EMPTY_ID
    ability_2_id: int = IdGenerator.EMPTY_ID
    ability_3_id: int = IdGenerator.EMPTY_ID
    ability_4_id: int = IdGenerator.EMPTY_ID

    def get_size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.hp))

    def get_spell_modifier(self) -> float:
        #calculation not yet implemented
        return 1.0

    def change_position(self, new_position_x: float, new_position_y: float) -> None:
        self.position_x = new_position_x
        self.position_y = new_position_y

    def suffer_damage(self, amount: float) -> None:
        self.hp -= amount

    def restore_health(self, amount: float) -> None:
        self.hp += amount


class CombatEvent(NamedTuple):
    event_id: int = IdGenerator.EMPTY_ID
    timestamp: float = 0.0
    source_id: int = IdGenerator.EMPTY_ID
    spell_id: int = IdGenerator.EMPTY_ID
    destination: Destination = Destination()


@dataclass
class CombatInstance:
    instance_id: int = IdGenerator.EMPTY_ID
    timestamp: float = 0.0
    update_interval: float = 1/30 #seconds between each update
    spells: Dict[int, Spell] = {}

    combat_objs: Dict[int, CombatObj] = {}
    spells: Dict[int, Spell] = {}
    combat_event_log: Dict[int, CombatEvent] = {}


    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells, f"Spell with ID {spell_id} not found."
        return self.spells.get(spell_id, Spell.create_empty())

    def add_spell(self, spell: Spell) -> None:
        assert spell.spell_id not in self.spells, f"Spell with ID {spell.spell_id} already exists."
        self.spells[spell.spell_id] = spell

    def register_input(self, combat_input: CombatInput) -> None:
        pass

    def update(self) -> None:
        pass
        #update_aura_timers_and_create_aura_events
        #process_combat_events

    def get_all_game_objs_to_draw(self) -> List[CombatObj]:
        return self.combat_handler.world.game_objs.values()