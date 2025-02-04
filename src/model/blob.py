from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
from typing import Any, Dict, List, Tuple, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json


@dataclass
class IdGen: #IdGenerator
    EMPTY_ID: ClassVar = 0
    _reserved_ids: Set[int] = set()
    _assigned_ids: Deque[int] = deque()

    @classmethod
    def preassign_id_range(cls, assigned_id_start: int, assigned_id_stop: int) -> 'IdGen':
        id_gen = IdGen()
        id_gen.assign_id_range(assigned_id_start, assigned_id_stop)
        return id_gen

    @staticmethod
    def is_empty_id(id_num: int) -> bool:
        return id_num == IdGen.EMPTY_ID

    def assign_id_range(self, start: int, stop: int) -> None:
        for id_num in range(start, stop):
            if id_num not in self._reserved_ids:
                self._assigned_ids.append(id_num)

    def new_id(self) -> int:
        assert self._assigned_ids
        if not self._assigned_ids:
            return IdGen.EMPTY_ID
        return self._assigned_ids.popleft()

    def reserve_id(self, reserved_id: int) -> None:
        self._reserved_ids.add(reserved_id)
        self._assigned_ids = deque(id_num for id_num in self._assigned_ids if id_num != reserved_id)


class Color:
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


class Spell(NamedTuple):
    spell_id: int = IdGen.EMPTY_ID
    preparation_id: int = IdGen.EMPTY_ID

    power: float = 1.0
    duration: float = 0.0
    ticks: int = 1

    flags: SpellFlag = SpellFlag.NONE

    #not yet implemeted
    #variance: float = 0
    #cost: float = 0
    #range_limit: float = 0
    #gcd_mod: float = 0.0
    #cast_time: float = 0.0
    #max_stacks: int = 1

    def has_preparation(self) -> bool:
        return not IdGen.is_empty_id(self.preparation_id)


class Aura(NamedTuple):
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    target_id: int = IdGen.EMPTY_ID
    start: float = 0.0
    end: float = 0.0
    ticks: int = 0

    @classmethod
    def create_aura(cls, source_id: int, spell: Spell, timestamp: float) -> None:
        return Aura(
            source_id=source_id,
            spell_id=spell.spell_id,
            start=timestamp,
            end=timestamp + spell.duration,
            ticks=spell.ticks,
        )

    def get_aura_id(self) -> Tuple[int, int, int]:
        return self.source_id, self.spell_id, self.target_id

    def get_duration(self) -> float:
        return self.end - self.start

    def get_tick_interval(self) -> float:
        return float('inf') if self.ticks == 0 else self.get_duration() / self.ticks

    def has_tick(self, last_visit: float, now: float) -> bool:
        """ Ticks happen every tick_interval seconds, excluding t=start, including t=end. """
        if last_visit >= self.end or now <= self.start:
            return False
        tick_interval = self.get_tick_interval()
        ticks_elapsed = max(0, (last_visit - self.start) / tick_interval)
        next_tick = self.start + (math.ceil(ticks_elapsed) * tick_interval)
        return (last_visit < next_tick <= now) and (next_tick <= self.end)


class GameInput(NamedTuple):
    timestamp: float = 0.0
    move_up: bool = False
    move_left: bool = False
    move_down: bool = False
    move_right: bool = False
    ability_1: bool = False
    ability_2: bool = False
    ability_3: bool = False
    ability_4: bool = False

    @classmethod
    def create_new_timestamp(cls, new_timestamp: float, other: 'GameInput') -> 'GameInput':
        return other._replace(timestamp=new_timestamp)

    def is_happening_now(self, last_visit: float, now: float) -> bool:
        return self.timestamp > last_visit and self.timestamp <= now

@dataclass
class Pos:
    target_id: int = IdGen.EMPTY_ID
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    size: float = 0.0

    def is_area(self) -> bool:
        return self.angle > 0.0 or self.size > 0.0


@dataclass
class Event:
    event_id: int = IdGen.EMPTY_ID
    timestamp: float = 0.0
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    dest: Pos = field(default_factory=Pos)

    @classmethod
    def create_combat_init(cls, event_id: int, timestamp: float, spell_id: int) -> 'Event':
        return Event(
            event_id=event_id,
            timestamp=timestamp,
            source_id=IdGen.EMPTY_ID,
            spell_id=spell_id,
            dest=Pos(target_id=IdGen.EMPTY_ID),
        )

    @classmethod
    def create_from_aura_tick(cls, event_id: int, timestamp: float, aura: Aura) -> 'Event':
        return Event(
            event_id=event_id,
            timestamp=timestamp,
            source_id=aura.source_id,
            spell_id=aura.spell_id,
            dest=Pos(target_id=aura.target_id),
        )

    def is_aoe(self) -> bool:
        return self.dest.is_area()

    def is_spawn_event(self) -> bool:
        return IdGen.is_empty_id(self.source_id)

    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.dest.target_id)

    def also_target(self, new_event_id: int, new_target_id: int) -> 'Event':
        event: Event = self.copy()
        event.event_id = new_event_id
        event.dest = Pos(target_id=new_target_id)
        return event

@dataclass
class Obj:
    obj_id: int = IdGen.EMPTY_ID
    npc_id: int = IdGen.EMPTY_ID

    hp: float = 0.0
    move_speed: float = 1.0
    is_attackable: bool = False

    custom_move_id: int = IdGen.EMPTY_ID
    move_up_id: int = IdGen.EMPTY_ID
    move_left_id: int = IdGen.EMPTY_ID
    move_down_id: int = IdGen.EMPTY_ID
    move_right_id: int = IdGen.EMPTY_ID
    slot_1_id: int = IdGen.EMPTY_ID
    slot_2_id: int = IdGen.EMPTY_ID
    slot_3_id: int = IdGen.EMPTY_ID
    slot_4_id: int = IdGen.EMPTY_ID

    pos: Pos = field(default_factory=Pos)
    game_inputs: SortedDict = field(default_factory=SortedDict)
    auras: Dict[int, Aura] = field(default_factory=dict)

    @classmethod
    def embody_npc(cls, unique_obj_id: int, other: 'Obj') -> 'Obj':
        new_obj: Obj = other.copy()
        new_obj.obj_id = unique_obj_id
        return new_obj

    def fetch_events(self, id_gen: IdGen, t_previous: float, t_next: float) -> List[Event]:
        events: List[Event] = []
        for aura in self.auras.values():
            if aura.has_tick(t_previous, t_next):
                assert aura.target_id == self.obj_id
                events.append(Event.create_from_aura_tick(id_gen.new_id(), t_next, aura))
        for timestamp in self.game_inputs.irange(t_previous, t_next, inclusive=(False, True)):
            game_input: GameInput = self.game_inputs[timestamp]
            events += InputHandler.convert_to_events(id_gen, t_next, self, game_input)
        for game_input in self.game_inputs.values():
            if game_input.is_happening_now(t_previous, t_next):
                events += InputHandler.convert_to_events(id_gen, t_next, self, game_input)
        return events

    def add_input(self, timestamp: float, new_input: GameInput) -> None:
        assert timestamp not in self.game_inputs, \
            f"Input for timestamp={timestamp} already exists in obj_id={self.obj_id}"
        self.game_inputs[timestamp] = new_input

    def is_npc(self) -> bool:
        return self.obj_id != self.npc_id

    def get_size(self) -> float:
        #fix later
        return 0.01 + math.sqrt(0.0001*abs(self.hp))

    def get_spell_modifier(self) -> float:
        #calculation not yet implemented
        return 1.0

    def teleport_to(self, new_x: float, new_y: float) -> None:
        self.pos.x = new_x
        self.pos.y = new_y

    def suffer_damage(self, amount: float) -> None:
        self.hp -= amount

    def restore_health(self, amount: float) -> None:
        self.hp += amount


@dataclass
class CombatInstance:
    instance_id: int = IdGen.EMPTY_ID
    prev_timestamp: float = 0.0
    next_timestamp: float = 0.0
    update_interval: float = 1/30 #seconds between each update
    update_accumulator: float = 0.0 #accumulated time since last update

    event_id_gen: IdGen = IdGen.preassign_id_range(1, 10_000)
    obj_id_gen: IdGen = IdGen.preassign_id_range(1, 10_000)

    player_obj: Obj = Obj()
    queued_input: GameInput = GameInput()

    objs: Dict[int, Obj] = {}
    event_log: Dict[int, Event] = {}

    def get_all_objs_to_draw(self) -> List[Obj]:
        return self.objs.values()

    def initialize_obj(self, spawn_id: int) -> None:
        event = Event.create_combat_init(self.event_id_gen.new_id(), self.next_timestamp, spawn_id)
        self._handle_event(event)

    def update(self, delta_time: float, game_input: GameInput) -> None:
        self.update_accumulator += delta_time
        self.queued_input = game_input
        while self.update_accumulator >= self.update_interval:
            self.player_obj.add_input(self.next_timestamp, self.queued_input)
            self.advance_combat()
            self.update_accumulator -= self.update_interval

    def advance_combat(self) -> None:
        events: List[Event] = []
        for obj in self.objs.values():
            events += obj.fetch_events(self.event_id_gen, self.prev_timestamp, self.next_timestamp)
        for event in events:
            self._handle_event(event)
        self.prev_timestamp = self.next_timestamp
        self.next_timestamp += self.update_interval

    def _handle_event(self, event: Event) -> None:
        if event.is_spawn_event():
            new_obj = SpawnHandler.spawn_obj(event)
            new_obj.obj_id = self.obj_id_gen.new_id()
            self._add_obj(new_obj)
        elif event.is_aoe():
            objs = AreaHandler.get_objs_in_area(event)
            for obj in objs:
                new_event = event.also_target(self.event_id_gen.new_id(), obj.obj_id)
                self._handle_event(new_event)
        else:
            source_obj = self._get_obj(event.source_id)
            target_obj = source_obj
            if event.has_target():
                target_obj = self._get_obj(event.dest.target_id)
            SpellHandler.handle_spell(event, source_obj, target_obj)
        self._log_event(event)

    def _add_obj(self, obj: Obj) -> None:
        assert obj.obj_id not in self.objs, f"Game object with ID {obj.obj_id} already exists."
        self.objs[obj.obj_id] = obj

    def _get_obj(self, obj_id: int) -> Obj:
        assert obj_id in self.objs, f"Game object with ID {obj_id} does not exist."
        return self.objs.get(obj_id, Obj())

    def _log_event(self, event: Event) -> None:
        assert event.event_id not in self.event_log, f"Game object with ID {event.event_id} already exists."
        self.event_log[event.event_id] = event


class InputHandler:

    @staticmethod
    def convert_to_events(id_gen: IdGen, timestamp: float, obj: Obj, game_input: GameInput) -> List[Event]:
        spell_ids: List[int] = []
        spell_ids += [obj.move_up_id] if game_input.move_up else []
        spell_ids += [obj.move_left_id] if game_input.move_left else []
        spell_ids += [obj.move_down_id] if game_input.move_down else []
        spell_ids += [obj.move_right_id] if game_input.move_right else []
        spell_ids += [obj.slot_1_id] if game_input.ability_1 else []
        spell_ids += [obj.slot_2_id] if game_input.ability_2 else []
        spell_ids += [obj.slot_3_id] if game_input.ability_3 else []
        spell_ids += [obj.slot_4_id] if game_input.ability_4 else []
        assert IdGen.EMPTY_ID not in spell_ids
        events: List[Event] = []
        for spell_id in spell_ids:
            events.append(Event(
                event_id=id_gen.new_id(),
                timestamp=timestamp,
                source_id=obj.obj_id,
                spell_id=spell_id,
                dest=obj.pos.copy(),
            ))
        return events


class SpawnHandler:

    @staticmethod
    def spawn_obj(event: Event) -> Obj:
        print(event.event_id) #remove pylint unused arg warning
        return Obj()


class AreaHandler:

    @staticmethod
    def get_objs_in_area(event: Event) -> List[Obj]:
        print(event.event_id) #remove pylint unused arg warning
        return []


class SpellHandler:

    @staticmethod
    def handle_spell(event: Event, source: Obj, target: Obj) -> None:
        print(event.event_id + source.source_id + target.obj_id) #remove pylint unused arg warning
        return


class Utils:

    @staticmethod
    def count_ticks_in_interval(t_start: float, t_stop: float, tick_interval: float) -> int:

        # Find the first tick after or at t_start
        first_tick = (t_start // tick_interval) * tick_interval
        if first_tick < t_start:
            first_tick += tick_interval

        # Find the last tick before or at t_stop
        last_tick = (t_stop // tick_interval) * tick_interval

        # If there are no ticks in the interval, return 0
        if first_tick > t_stop:
            return 0

        # Calculate number of ticks
        num_ticks = int((last_tick - first_tick) / tick_interval) + 1

        return num_ticks