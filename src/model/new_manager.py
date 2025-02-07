from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
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


class IdGen:
    EMPTY_ID = 0

    def __init__(self) -> None:
        self._reserved_ids: Set[int] = set()
        self._assigned_ids: Deque[int] = deque()

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
        if not self._assigned_ids:
            assert self._assigned_ids
            return IdGen.EMPTY_ID
        return self._assigned_ids.popleft()

    def reserve_id(self, reserved_id: int) -> None:
        self._reserved_ids.add(reserved_id)
        self._assigned_ids = deque(id_num for id_num in self._assigned_ids if id_num != reserved_id)


class SpellFlag(Flag):
    NONE = 0
    MOVE_UP = auto()
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
    SPAWN_NPC = auto()
    SPAWN_PLAYER = auto()
    AURA = auto()


class Spell(NamedTuple):
    spell_id: int = IdGen.EMPTY_ID
    effect_id: int = IdGen.EMPTY_ID

    power: float = 1.0
    #self.variance: float = 0 #not yet implemeted

    #self.cost: float = 0 #not yet implemented
    #self.range_limit: float = 0 #not yet implemented
    #self.gcd_mod: float = 0.0 #not yet implemented
    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 1

    flags: SpellFlag = SpellFlag.NONE

    def copy(self) -> 'Spell':
        return copy(self)

    def has_npc_to_spawn(self) -> bool:
        return self.flags & SpellFlag.SPAWN_NPC or self.flags & SpellFlag.SPAWN_PLAYER

    def has_aura_to_apply(self) -> bool:
        return self.flags & SpellFlag.AURA

    def has_effect(self) -> bool:
        return not IdGen.is_empty_id(self.effect_id)


class Aura(NamedTuple):
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    target_id: int = IdGen.EMPTY_ID
    start: float = 0.0
    end: float = 0.0
    ticks: int = 0

    @classmethod
    def create_aura(cls, timestamp: float, source_id: int, spell: Spell, target_id: int) -> None:
        return Aura(
            source_id=source_id,
            spell_id=spell.spell_id,
            target_id=target_id,
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


@dataclass
class Dest:
    target_id: int = IdGen.EMPTY_ID
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    size: float = 0.0

    def copy(self) -> 'Dest':
        return copy(self)

    def move_in_direction(self, direction: 'Dest', modifier: float, delta_time: float) -> None:
        self.x += direction.x * modifier * delta_time
        self.y += direction.y * modifier * delta_time

    def has_position(self) -> bool:
        return self.x != 0.0 and self.y != 0.0

    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.target_id)


class GameInput(NamedTuple):
    local_timestamp: float = 0.0
    move_up: bool = False
    move_left: bool = False
    move_down: bool = False
    move_right: bool = False
    ability_1: bool = False
    ability_2: bool = False
    ability_3: bool = False
    ability_4: bool = False

    def is_happening_now(self, last_visit: float, now: float) -> bool:
        return self.local_timestamp > last_visit and self.local_timestamp <= now


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = 1
    FAILED = 2
    MISSED = 3


@dataclass
class CombatEvent:
    event_id: Final[int] = IdGen.EMPTY_ID
    timestamp: float = 0.0
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    dest: Dest = field(default_factory=Dest)
    outcome: EventOutcome = EventOutcome.EMPTY

    @classmethod
    def create_from_aura_tick(cls, event_id: int, timestamp: float, aura: Aura) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            source_id=aura.source_id,
            spell_id=aura.spell_id,
            dest=Dest(target_id=aura.target_id),
        )

    def copy(self) -> 'CombatEvent':
        return copy(self)

    def get_event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] obj_{self.source_id:04d} uses spell_{self.spell_id:04d} on obj_{self.dest.target_id:04d} at (x={self.dest.x:.3f}, y={self.dest.y:.3f})"

    def decide_outcome(self) -> None:
        #not implemented
        self.outcome = EventOutcome.SUCCESS

    def is_aoe(self) -> bool:
        return False #fix later

    def is_spawn_event(self) -> bool:
        return IdGen.is_empty_id(self.source_id)

    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.dest.target_id)

    def also_spell_effect(self, new_event_id: int, new_spell_id: int) -> 'CombatEvent':
        new_event: CombatEvent = self.copy()
        new_event.event_id = new_event_id
        new_event.spell_id = new_spell_id
        return new_event

    def also_target(self, new_event_id: int, new_target_id: int) -> 'CombatEvent':
        new_event: CombatEvent = self.copy()
        new_event.event_id = new_event_id
        new_event.dest = Dest(target_id=new_target_id)
        return new_event


@dataclass
class GameObj:
    obj_id: Final[int] = IdGen.EMPTY_ID
    position: Dest = field(default_factory=Dest)
    parent_id: int = IdGen.EMPTY_ID
    npc_id: int = IdGen.EMPTY_ID
    hp: float = 0.0
    movement_speed: float = 1.0
    is_attackable: bool = False
    is_player: bool = False

    # Ability slots
    move_up_id: int = IdGen.EMPTY_ID
    move_left_id: int = IdGen.EMPTY_ID
    move_down_id: int = IdGen.EMPTY_ID
    move_right_id: int = IdGen.EMPTY_ID
    slot_1_id: int = IdGen.EMPTY_ID
    slot_2_id: int = IdGen.EMPTY_ID
    slot_3_id: int = IdGen.EMPTY_ID
    slot_4_id: int = IdGen.EMPTY_ID

    game_inputs: SortedDict[float, GameInput] = field(default_factory=SortedDict)
    auras: Dict[int, Aura] = field(default_factory=dict)

    @classmethod
    def embody_npc(cls, unique_obj_id: int, parent_id: int, other: 'GameObj') -> 'GameObj':
        new_obj: GameObj = other.copy()
        new_obj.obj_id = unique_obj_id
        new_obj.parent_id = parent_id
        return new_obj

    def fetch_events(self, id_gen: IdGen, t_previous: float, t_next: float) -> List[CombatEvent]:
        events: List[CombatEvent] = []
        for aura in self.auras.values():
            if aura.has_tick(t_previous, t_next):
                assert aura.target_id == self.obj_id
                events.append(CombatEvent.create_from_aura_tick(id_gen.new_id(), t_next, aura))
        for timestamp in self.game_inputs.irange(t_previous, t_next, inclusive=(False, True)):
            game_input: GameInput = self.game_inputs[timestamp]
            events += InputHandler.convert_to_events(id_gen, t_next, self, game_input)
        return events

    def add_input(self, timestamp: float, new_input: GameInput) -> None:
        assert timestamp not in self.game_inputs, \
            f"Input for timestamp={timestamp} already exists in obj_id={self.obj_id}"
        self.game_inputs[timestamp] = new_input

    def add_aura(self, aura: Aura) -> None:
        assert aura.get_aura_id() not in self.auras, f"Aura with ID ({aura.get_aura_id()}) already exists."
        self.auras[aura.get_aura_id()] = aura

    def get_aura(self, aura_id: Tuple[int, int, int]) -> Aura:
        assert aura_id in self.auras, f"Aura with ID ({aura_id}) does not exist."
        return self.auras.get(aura_id, Aura())

    def copy(self) -> 'GameObj':
        return copy(self)

    def get_size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.hp))

    def get_spell_modifier(self) -> float:
        #calculation not yet implemented
        return 1.0

    def teleport_to(self, new_position: Dest) -> None:
        self.position.x = new_position.x
        self.position.y = new_position.y

    def suffer_damage(self, spell_power: float) -> None:
        self.hp -= spell_power

    def restore_health(self, spell_power: float) -> None:
        self.hp += spell_power


class Ruleset:
    """ Immutable data related to game configuration """
    def __init__(self) -> None:
        self.npcs: Dict[int, GameObj] = {}
        self.spells: Dict[int, Spell] = {}
        self.populate_ruleset()

    def get_npc(self, npc_id: int) -> GameObj:
        assert npc_id in self.npcs, f"Npc with ID {npc_id} not found."
        return self.npcs.get(npc_id, GameObj())

    def add_npc(self, npc: GameObj) -> None:
        assert npc.npc_id not in self.npcs, f"Npc with ID {npc.npc_id} already exists."
        self.npcs[npc.npc_id] = npc

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells, f"Spell with ID {spell_id} not found."
        return self.spells.get(spell_id, Spell())

    def add_spell(self, spell: Spell) -> None:
        assert spell.spell_id not in self.spells, f"Spell with ID {spell.spell_id} already exists."
        self.spells[spell.spell_id] = spell

    def populate_ruleset(self) -> None:
        database = Database()
        for npc in database.npcs:
            self.add_npc(npc)
        for spell in database.spells:
            self.add_spell(spell)


class EventLog:
    def __init__(self) -> None:
        self._combat_event_log: Dict[int, CombatEvent] = {}

    def add_event(self, combat_event: CombatEvent):
        self._combat_event_log[combat_event.event_id] = combat_event
        print(combat_event.get_event_summary())


class World:
    """ The entire world state """
    def __init__(self) -> None:
        self.previous_timestamp: float = 0.0
        self.current_timestamp: float = 0.0
        self.delta_time: float = 0.0  # to be deleted

        self.aura_id_gen: IdGen = IdGen.preassign_id_range(1, 10_000)
        self.event_id_gen: IdGen = IdGen.preassign_id_range(1, 1000)
        self.game_obj_id_gen: IdGen = IdGen.preassign_id_range(1, 10_000)

        self.player_obj: GameObj = GameObj()

        self.ruleset: Ruleset = Ruleset()
        self.auras: Dict[Tuple[int, int, int], Aura] = {}
        self.game_objs: Dict[int, GameObj] = {}
        self.root_obj_id: int = IdGen.EMPTY_ID
        self.combat_event_log: EventLog = EventLog()

    @classmethod
    def create_empty(cls) -> 'World':
        return World()

    @classmethod
    def create_with_root_obj(cls) -> 'World':
        world = World()
        root_obj_id = world.game_obj_id_gen.new_id()
        world.add_game_obj(GameObj(root_obj_id, Dest()))
        world.root_obj_id = root_obj_id
        return world

    def advance_combat(self, delta_time: float, game_input: GameInput) -> None:
        self.current_timestamp = self.previous_timestamp + delta_time
        self.player_obj.add_input(self.current_timestamp, game_input)
        events: List[CombatEvent] = []
        for obj in self.game_objs.values():
            events += obj.fetch_events(self.event_id_gen, self.previous_timestamp, self.current_timestamp)
        for event in events:
            self._handle_event(event)
        self.previous_timestamp = self.current_timestamp

    def _handle_event(self, event: CombatEvent) -> None:
        source_obj = self.get_game_obj(event.source_id)
        spell = self.ruleset.get_spell(event.spell_id)
        target_position = event.dest.copy()
        target_obj = source_obj
        if event.dest.has_target():
            target_obj = self.get_game_obj(event.dest.target_id)
        if not event.dest.has_target() and event.dest.has_position():
            # not yet implemented, but create new event on each target within position
            pass
        event.decide_outcome()
        if event.outcome == EventOutcome.SUCCESS:
            if spell.has_effect():
                new_event = event.also_spell_effect(self.event_id_gen.new_id(), spell.effect_id)
                self._handle_event(new_event)
            SpellHandler.handle_spell(source_obj, spell, target_obj, target_position, self)
        self.combat_event_log.add_event(event)

    def add_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self.game_objs, f"Game object with ID {game_obj.obj_id} already exists."
        self.game_objs[game_obj.obj_id] = game_obj

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self.game_objs, f"Game object with ID {obj_id} does not exist."
        return self.game_objs.get(obj_id, GameObj())

    def get_delta_time(self) -> float:
        return self.current_timestamp - self.previous_timestamp



class PlayerInputHandler:
    def __init__(self) -> None:
        self.event_id_gen: IdGen = IdGen.preassign_id_range(1000, 10_000)
        self.combat_events: List[CombatEvent] = []
        self.player_obj: GameObj = GameObj()
        self.movement_spell_id: int = Database.player_move_up().spell_id
        self.ability_1_spell_id: int = Database.fireblast().spell_id
        self.ability_2_spell_id: int = Database.fireblast().spell_id
        self.ability_3_spell_id: int = Database.fireblast().spell_id
        self.ability_4_spell_id: int = Database.fireblast().spell_id
        self.current_timestamp: float = 0.0
        self.is_pressing_move_up: bool = False
        self.is_pressing_move_left: bool = False
        self.is_pressing_move_down: bool = False
        self.is_pressing_move_right: bool = False
        self.is_pressing_ability_1: bool = False
        self.is_pressing_ability_2: bool = False
        self.is_pressing_ability_3: bool = False
        self.is_pressing_ability_4: bool = False

    def update_input(self, delta_time: float, move_up: bool, move_left: bool, move_down: bool, move_right: bool, ability_1: bool, ability_2: bool, ability_3: bool, ability_4: bool) -> None:
        self.current_timestamp += delta_time
        self.is_pressing_move_up = move_up
        self.is_pressing_move_left = move_left
        self.is_pressing_move_down = move_down
        self.is_pressing_move_right = move_right
        self.is_pressing_ability_1 = ability_1
        self.is_pressing_ability_2 = ability_2
        self.is_pressing_ability_3 = ability_3
        self.is_pressing_ability_4 = ability_4
        self._process_input()

    def fetch_combat_events(self) -> List[CombatEvent]:
        combat_events = self.combat_events.copy()
        self.combat_events.clear()
        return combat_events

    def set_player_obj(self, player_obj: GameObj) -> None:
        self.player_obj = player_obj

    def _process_input(self) -> None:
        if self._is_moving():
            pos = Dest()
            if self.is_pressing_move_up:
                pos.y += 1.0
            if self.is_pressing_move_left:
                pos.x -= 1.0
            if self.is_pressing_move_down:
                pos.y -= 1.0
            if self.is_pressing_move_right:
                pos.x += 1.0
            self._create_event(self.movement_spell_id, pos)
        target_id = self.player_obj.position.target_id
        if self.is_pressing_ability_1:
            self._create_event(self.ability_1_spell_id, Dest(target_id=target_id))
        if self.is_pressing_ability_2:
            self._create_event(self.ability_2_spell_id, Dest(target_id=target_id))
        if self.is_pressing_ability_3:
            self._create_event(self.ability_3_spell_id, Dest(target_id=target_id))
        if self.is_pressing_ability_4:
            self._create_event(self.ability_4_spell_id, Dest(target_id=target_id))


    def _is_moving(self) -> bool:
        return (self.is_pressing_move_up or
                self.is_pressing_move_down or
                self.is_pressing_move_left or
                self.is_pressing_move_right)

    def _create_event(self, spell_id: int, dest: Dest) -> None:
        event_id = self.event_id_gen.new_id()
        timestamp = self.current_timestamp
        source_id = self.player_obj.obj_id
        self.combat_events.append(CombatEvent(event_id, timestamp, source_id, spell_id, dest))


class CombatHandler:
    def __init__(self) -> None:
        self.world: World = World.create_with_root_obj()
        self.current_events: Deque[CombatEvent] = deque()

    def load_zone(self, spell_id: int) -> None:
        zone_setup_event = CombatEvent(
            event_id=self.world.event_id_gen.new_id(),
            timestamp=self.world.previous_timestamp,
            source_id=self.world.root_obj_id,
            spell_id=spell_id,
        )
        self.current_events.append(zone_setup_event)
        self.process_combat()

    def read_player_input_events(self, combat_events: List[CombatEvent]) -> None:
        self.current_events.extend(combat_events)

    def update_world_timer_and_create_aura_events(self, delta_time: float) -> None:
        self.world.delta_time = delta_time
        self.world.previous_timestamp += self.world.delta_time
        aura_ids: List[Tuple[int, int, int]] = sorted(self.world.auras.keys())
        for aura_id in aura_ids:
            aura = self.world.get_aura(aura_id)
            if aura.has_tick(self.world.previous_timestamp - delta_time, self.world.previous_timestamp):
                # Only process one aura tick per server tick
                self.add_event(aura.source_id, aura.spell_id, Dest(target_id=aura.target_id))

    def add_event(self, source_id: int, spell_id: int, dest: Dest) -> None:
        event = CombatEvent(self.world.event_id_gen.new_id(), self.world.previous_timestamp, source_id, spell_id, dest)
        self.current_events.append(event)

    def get_player_obj(self) -> GameObj:
        for game_obj in self.world.game_objs.values():
            if game_obj.is_player is True:
                return game_obj
        assert False, "Player object not found."
        return GameObj.create_empty()

    def process_combat(self) -> None:
        event_limit = 1000 # This failsafe should never be reached in-game
        while len(self.current_events) > 0 or event_limit <= 0:
            event_limit -= 1
            event = self.current_events.popleft()
            self.world._handle_event(event)


class SpellHandler:
    @staticmethod
    def handle_spell(source_obj: GameObj, spell: Spell, target_obj: GameObj, pos: Dest, world: World) -> None:
        if spell.has_npc_to_spawn():
            obj_id = world.game_obj_id_gen.new_id()
            npc_template = world.ruleset.get_npc(spell.spell_id)
            new_obj = GameObj.embody_npc(obj_id, source_obj.obj_id, npc_template)
            world.add_game_obj(new_obj)
            if spell.flags & SpellFlag.SPAWN_PLAYER:
                world.player_obj = new_obj
        if spell.has_aura_to_apply():
            aura_spell = world.ruleset.get_spell(spell.effect_id)
            aura_dest = Dest(target_id=target_obj.obj_id)
            aura = Aura.create_aura(world.current_timestamp, source_obj.obj_id, aura_spell, aura_dest.target_id)
            target_obj.add_aura(aura)

        # Handle spell flags
        if spell.flags & SpellFlag.FIND_TARGET:
            for game_obj in world.game_objs.values():
                if game_obj.is_attackable and (game_obj.is_player != source_obj.is_player):
                    source_obj.position.target_id = game_obj.obj_id
        if spell.flags & SpellFlag.MOVE_UP:
            #direction = pos
            direction_up = Dest(x=0.0, y=1.0)
            source_obj.position.move_in_direction(direction_up, target_obj.movement_speed, world.get_delta_time())
        if spell.flags & SpellFlag.DAMAGE:
            spell_power = spell.power * source_obj.get_spell_modifier()
            target_obj.suffer_damage(spell_power)
        if spell.flags & SpellFlag.HEAL:
            spell_power = spell.power * source_obj.get_spell_modifier()
            target_obj.restore_health(spell_power)


class InputHandler:

    @staticmethod
    def convert_to_events(id_gen: IdGen, timestamp: float, obj: GameObj, game_input: GameInput) -> List[CombatEvent]:
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
        events: List[CombatEvent] = []
        for spell_id in spell_ids:
            events.append(CombatEvent(
                event_id=id_gen.new_id(),
                timestamp=timestamp,
                source_id=obj.obj_id,
                spell_id=spell_id,
                dest=obj.position.copy(),
            ))
        return events


class GameManager:
    def __init__(self) -> None:
        self.combat_handler: CombatHandler = CombatHandler()
        self.player_input_handler: PlayerInputHandler = PlayerInputHandler()

    def simulate_game_in_console(self) -> None:
        self.setup_game(1)
        SIMULATION_DURATION = 5
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of player input
            self.process_server_tick(1 / UPDATES_PER_SECOND, True, False, False, False, True, False, False, False)

    def setup_game(self, setup_spell_id: int) -> None:
        self.combat_handler.load_zone(setup_spell_id)
        player_obj = self.combat_handler.get_player_obj()
        self.player_input_handler.set_player_obj(player_obj)

    def process_server_tick(self, delta_time: float, move_up: bool, move_left: bool, move_down: bool, move_right: bool, ability_1: bool, ability_2: bool, ability_3: bool, ability_4: bool) -> None:
        self.player_input_handler.update_input(delta_time, move_up, move_left, move_down, move_right, ability_1, ability_2, ability_3, ability_4)
        events_from_player = self.player_input_handler.fetch_combat_events()
        #self.combat_handler.read_player_input_events(events_from_player)

        self.combat_handler.world.advance_combat(delta_time, GameInput(local_timestamp=self.combat_handler.world.current_timestamp, move_up=move_up, move_left=move_left, move_down=move_down, move_right=move_right, ability_1=ability_1, ability_2=ability_2, ability_3=ability_3, ability_4=ability_4))
        #self.combat_handler.update_world_timer_and_create_aura_events(delta_time)
        #self.combat_handler.process_combat()

    def get_all_game_objs_to_draw(self) -> List[GameObj]:
        return self.combat_handler.world.game_objs.values()


class Serializer:
    @staticmethod
    def to_json(instance: Any) -> str:
        """ Creates a json string, ignoring properties with default values."""
        default_instance = instance.__class__.create_empty()
        diff_dict = {
            key: value
            for key, value in instance.__dict__.items()
            if value != default_instance.__dict__[key]
        }
        return json.dumps(diff_dict)

    @staticmethod
    def from_json(serialized_cls: type, json_str: str) -> Any:
        """ Creates an instance from json string, ignoring mismatching properties. """
        default_instance = serialized_cls.create_empty()
        json_data = json.loads(json_str)
        for key, value in json_data.items():
            if hasattr(default_instance, key):
                setattr(default_instance, key, value)
        return default_instance


class Database:
    def __init__(self) -> None:
        self.npcs: List[GameObj] = [
            Database.empty_npc(),
            Database.test_player(),
            Database.test_enemy(),
        ]
        self.spells: List[Spell] = [
            Database.empty_spell(),
            Database.player_move_up(),
            Database.fireblast(),
            Database.humble_heal(),
            Database.blessed_aura(),
            Database.spawn_player(),
            Database.spawn_enemy(),
            Database.setup_test_zone(),
        ]

    # Spells
    @staticmethod
    def empty_spell() -> Spell:
        return Spell(
            spell_id=0,
        )

    @staticmethod
    def player_move_up() -> Spell:
        return Spell(
            spell_id=1,
            flags=SpellFlag.MOVE_UP | SpellFlag.STOP_CAST
        )

    @staticmethod
    def fireblast() -> Spell:
        return Spell(
            spell_id=2,
            power=3.0,
            flags=SpellFlag.DAMAGE | SpellFlag.FIND_TARGET,
        )

    @staticmethod
    def humble_heal() -> Spell:
        return Spell(
            spell_id=3,
            duration=30.0,
            ticks=50,
            power=200.0,
            flags=SpellFlag.HEAL,
        )


    @staticmethod
    def blessed_aura() -> Spell:
        return Spell(
            spell_id=4,
            effect_id=Database.humble_heal().spell_id,
            flags=SpellFlag.AURA,
        )

    @staticmethod
    def spawn_player() -> Spell:
        return Spell(
            spell_id=Database.test_player().npc_id,
            effect_id=Database.spawn_enemy().spell_id,
            flags=SpellFlag.SPAWN_PLAYER,
        )

    @staticmethod
    def spawn_enemy() -> Spell:
        return Spell(
            spell_id=Database.test_enemy().npc_id,
            flags=SpellFlag.SPAWN_NPC,
        )

    @staticmethod
    def setup_test_zone() -> Spell:
        return Spell(
            spell_id=10,
            effect_id=Database.spawn_player().spell_id,
        )

    # Npcs
    @staticmethod
    def empty_npc() -> GameObj:
        return GameObj(
            npc_id=6,
        )

    @staticmethod
    def test_player() -> GameObj:
        return GameObj(
            npc_id=7,
            hp=30.0,
            is_player=True,
            position=Dest(x=0.3, y=0.3),
            move_up_id=Database.player_move_up().spell_id,
            move_left_id=Database.player_move_up().spell_id,
            move_down_id=Database.player_move_up().spell_id,
            move_right_id=Database.player_move_up().spell_id,
            slot_1_id=Database.fireblast().spell_id,
            slot_2_id=Database.fireblast().spell_id,
            slot_3_id=Database.fireblast().spell_id,
            slot_4_id=Database.fireblast().spell_id,
        )

    @staticmethod
    def test_enemy() -> GameObj:
        game_inputs: SortedDict[float, GameInput] = SortedDict()
        input_1 = GameInput(local_timestamp=3.0, ability_1=True)
        input_2 = GameInput(local_timestamp=5.0, ability_2=True)
        game_inputs[input_1.local_timestamp] = input_1
        game_inputs[input_2.local_timestamp] = input_2
        return GameObj(
            npc_id=8,
            hp=30.0,
            is_player=False,
            position=Dest(x=0.7, y=0.7),
            slot_1_id=Database.humble_heal().spell_id,
            slot_2_id=Database.blessed_aura().spell_id,
            game_inputs=game_inputs,
        )


#%%
if __name__ == "__main__":
    manager = GameManager()
    manager.simulate_game_in_console()