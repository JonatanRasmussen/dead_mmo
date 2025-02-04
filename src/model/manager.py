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

    def __init__(self) -> None:
        self._reserved_ids: Set[int] = set()
        self._assigned_ids: Deque[int] = deque()

    @classmethod
    def preassign_id_range(cls, assigned_id_start: int, assigned_id_stop: int) -> 'IdGenerator':
        id_gen = IdGenerator()
        id_gen.assign_id_range(assigned_id_start, assigned_id_stop)
        return id_gen

    @staticmethod
    def is_empty_id(id_num: int) -> bool:
        return id_num == IdGenerator.EMPTY_ID

    def assign_id_range(self, start: int, stop: int) -> None:
        for id_num in range(start, stop):
            if id_num not in self._reserved_ids:
                self._assigned_ids.append(id_num)

    def new_id(self) -> int:
        if not self._assigned_ids:
            assert self._assigned_ids
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
    def is_equal(self, other: 'Spell') -> bool:
        return self.spell_id == other.spell_id
    def is_empty(self) -> bool:
        return self.spell_id == IdGenerator.EMPTY_ID

    def has_npc_to_spawn(self) -> bool:
        return self.spawn_npc_id != IdGenerator.EMPTY_ID

    def has_aura_to_apply(self) -> bool:
        return self.aura_spell_id != IdGenerator.EMPTY_ID

    def has_cascade_spell(self) -> bool:
        return self.cascade_spell_id != IdGenerator.EMPTY_ID

    def has_disabling_spell(self) -> bool:
        return self.disabling_spell_id != IdGenerator.EMPTY_ID


@dataclass
class Dest:
    target_id: int = IdGenerator.EMPTY_ID
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
        return not IdGenerator.is_empty_id(self.target_id)


class Aura:
    def __init__(self, aura_id: int, source_id: int, spell: Spell, target_id: int) -> None:
        self.aura_id: Final[int] = aura_id
        self.source_id: Final[int] = source_id
        self.spell_id: Final[int] = spell.spell_id
        self.spell_duration: Final[float] = spell.duration
        self.spell_ticks: Final[int] = spell.ticks
        self.spell_max_stacks: Final[int] = spell.max_stacks
        self.target_id: Final[int] = target_id

        self.activation_delay: float = 0.0
        self.time_remaining: float = 0.0
        self.stacks: int = 0
        self.tick_interval: float = 0.0
        self.time_since_last_tick: float = 0.0
        self.ticks_awaiting_processing: int = 0

    @classmethod
    def create_empty(cls) -> 'Aura':
        return Aura(IdGenerator.EMPTY_ID, IdGenerator.EMPTY_ID, Spell(), IdGenerator.EMPTY_ID)
    def copy(self) -> 'Aura':
        return copy(self)
    def is_equal(self, other: 'Aura') -> bool:
        return self.aura_id == other.aura_id
    def is_empty(self) -> bool:
        return self.aura_id == IdGenerator.EMPTY_ID

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
        self.tick_interval = self.time_remaining / max(1, self.spell_ticks) #Avoid division by 0

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
            self.time_remaining: float = 0.0
            self.stacks: int = 0
            self.tick_interval: float = 0.0
            self.time_since_last_tick: float = 0.0

    def try_process_tick(self) -> bool:
        if self.ticks_awaiting_processing > 0:
            self.ticks_awaiting_processing -= 1
            return True
        return False


class Npc:
    def __init__(self, npc_id: int) -> None:
        self.npc_id: Final[int] = npc_id
        self.hp: float = 0.0
        self.movement_speed: float = 1.0
        self.is_attackable: bool = False
        self.is_player: bool = False

    @classmethod
    def create_empty(cls) -> 'Npc':
        return Npc(IdGenerator.EMPTY_ID)
    def copy(self) -> 'Npc':
        return copy(self)
    def is_equal(self, other: 'Npc') -> bool:
        return self.__dict__ == other.__dict__
    def is_empty(self) -> bool:
        return self.npc_id == IdGenerator.EMPTY_ID


class GameObj:
    def __init__(self, obj_id: int, position: Dest) -> None:
        self.obj_id: Final[int] = obj_id
        self.parent_id: int = IdGenerator.EMPTY_ID
        self.npc_properties: Npc = Npc.create_empty()
        self.position: Dest = position.copy()
        self.destination: Dest = Dest()
        self.hp: float = 0.0
        self.movement_speed: float = 1.0
        self.is_attackable: bool = False
        self.is_player: bool = False

    @classmethod
    def create_empty(cls) -> 'GameObj':
        return GameObj(IdGenerator.EMPTY_ID, Dest())
    def is_equal(self, other: 'GameObj') -> bool:
        return self.obj_id == other.obj_id
    def is_empty(self) -> bool:
        return self.obj_id == IdGenerator.EMPTY_ID

    def load_npc_data(self, npc: Npc) -> None:
        self.npc_properties = npc
        self.hp = npc.hp
        self.is_attackable = npc.is_attackable
        self.is_player = npc.is_player

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


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = 1
    FAILED = 2
    MISSED = 3

class CombatEvent:
    def __init__(self, event_id: int, timestamp: float, source_id: int, spell_id: int, dest: Dest) -> None:
        self.event_id: Final[int] = event_id
        self.timestamp: float = timestamp
        self.source_id: int = source_id
        self.spell_id: int = spell_id
        self.dest: Dest = dest.copy()
        self.outcome: EventOutcome = EventOutcome.EMPTY

    @classmethod
    def create_empty(cls) -> 'CombatEvent':
        return CombatEvent(IdGenerator.EMPTY_ID, 0.0, IdGenerator.EMPTY_ID, IdGenerator.EMPTY_ID, Dest())
    def is_equal(self, other: 'CombatEvent') -> bool:
        return self.event_id == other.event_id
    def is_empty(self) -> bool:
        return self.event_id == IdGenerator.EMPTY_ID

    def get_event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] obj_{self.source_id:04d} uses spell_{self.spell_id:04d} on obj_{self.dest.target_id:04d} at (x={self.dest.x:.3f}, y={self.dest.y:.3f})"

    def decide_outcome(self) -> None:
        #not implemented
        self.outcome = EventOutcome.SUCCESS


class Zone:
    def __init__(self, zone_id: int) -> None:
        self.zone_id: Final[int] = zone_id
        self.player_spawn: Tuple[int, Dest] = (IdGenerator.EMPTY_ID, Dest())
        self.enemy_spawn: Tuple[int, Dest] = (IdGenerator.EMPTY_ID, Dest())

    @classmethod
    def create_empty(cls) -> 'Zone':
        return Zone(IdGenerator.EMPTY_ID)
    def is_equal(self, other: 'Zone') -> bool:
        return self.zone_id == other.zone_id
    def is_empty(self) -> bool:
        return self.zone_id == IdGenerator.EMPTY_ID

    def fetch_player(self) -> Tuple[int, Dest]:
        return (self.player_spawn[0], self.player_spawn[1].copy())

    def fetch_enemy(self) -> Tuple[int, Dest]:
        return (self.enemy_spawn[0], self.enemy_spawn[1].copy())

    def set_player(self, spell_id: int, pos_x: float, pos_y: float) -> None:
        self.player_spawn = (spell_id, Dest(x=pos_x, y=pos_y))

    def set_enemy(self, spell_id: int, pos_x: float, pos_y: float) -> None:
        self.enemy_spawn = (spell_id, Dest(x=pos_x, y=pos_y))


class Ruleset:
    """ Immutable data related to game configuration """
    def __init__(self) -> None:
        self.npcs: Dict[int, Npc] = {}
        self.spells: Dict[int, Spell] = {}
        self.zones: Dict[int, Zone] = {}
        self.populate_ruleset()

    def get_npc(self, npc_id: int) -> Npc:
        assert npc_id in self.npcs, f"Npc with ID {npc_id} not found."
        return self.npcs.get(npc_id, Npc.create_empty())

    def add_npc(self, npc: Npc) -> None:
        assert npc.npc_id not in self.npcs, f"Npc with ID {npc.npc_id} already exists."
        self.npcs[npc.npc_id] = npc

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells, f"Spell with ID {spell_id} not found."
        return self.spells.get(spell_id, Spell())

    def add_spell(self, spell: Spell) -> None:
        assert spell.spell_id not in self.spells, f"Spell with ID {spell.spell_id} already exists."
        self.spells[spell.spell_id] = spell

    def get_zone(self, zone_id: int) -> Zone:
        assert zone_id in self.zones, f"Zone with ID {zone_id} not found."
        return self.zones.get(zone_id, Zone.create_empty())

    def add_zone(self, zone: Zone) -> None:
        assert zone.zone_id not in self.zones, f"Zone with ID {zone.zone_id} already exists."
        self.zones[zone.zone_id] = zone

    def populate_ruleset(self) -> None:
        database = Database()
        for npc in database.npcs:
            self.add_npc(npc)
        for spell in database.spells:
            self.add_spell(spell)
        for zone in database.zones:
            self.add_zone(zone)


class EventLog:
    def __init__(self) -> None:
        self._combat_event_log: Dict[int, CombatEvent] = {}

    def add_event(self, combat_event: CombatEvent):
        self._combat_event_log[combat_event.event_id] = combat_event
        print(combat_event.get_event_summary())


class World:
    """ The entire world state """
    def __init__(self) -> None:
        self.timestamp: float = 0.0
        self.delta_time: float = 0.0
        self.ruleset: Ruleset = Ruleset()
        self.auras: Dict[int, Aura] = {}
        self.game_objs: Dict[int, GameObj] = {}
        self.root_obj_id: int = IdGenerator.EMPTY_ID
        self.combat_event_log: EventLog = EventLog()

    @classmethod
    def create_empty(cls) -> 'World':
        return World()

    @classmethod
    def create_with_root_obj(cls, root_obj_id: int) -> 'World':
        world = World()
        world.add_game_obj(GameObj(root_obj_id, Dest()))
        world.root_obj_id = root_obj_id
        return world

    def add_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self.game_objs, f"Game object with ID {game_obj.obj_id} already exists."
        self.game_objs[game_obj.obj_id] = game_obj

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self.game_objs, f"Game object with ID {obj_id} does not exist."
        return self.game_objs.get(obj_id, GameObj.create_empty())

    def add_aura(self, aura: Aura) -> None:
        assert aura.aura_id not in self.auras, f"Aura with ID {aura.aura_id} already exists."
        self.auras[aura.aura_id] = aura

    def get_aura(self, aura_id: int) -> Aura:
        assert aura_id in self.auras, f"Aura with ID {aura_id} does not exist."
        return self.auras.get(aura_id, Aura.create_empty())

    def aura_exists(self, spell_id: int, target_id: int) -> bool:
        for aura in self.auras.values():
            if aura.spell_id == spell_id and aura.target_id == target_id and aura.is_active():
                return True
        return False


class PlayerInputHandler:
    def __init__(self) -> None:
        self.event_id_gen: IdGenerator = IdGenerator.preassign_id_range(1000, 10_000)
        self.combat_events: List[CombatEvent] = []
        self.player_obj: GameObj = GameObj.create_empty()
        self.movement_spell_id: int = Database.player_movement().spell_id
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
        target_id = self.player_obj.destination.target_id
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
        self.aura_id_gen: IdGenerator = IdGenerator.preassign_id_range(1, 10_000)
        self.event_id_gen: IdGenerator = IdGenerator.preassign_id_range(1, 1000)
        self.game_obj_id_gen: IdGenerator = IdGenerator.preassign_id_range(1, 10_000)
        self.world: World = World.create_with_root_obj(self.game_obj_id_gen.new_id())
        self.current_events: Deque[CombatEvent] = deque()

    def load_zone(self, zone_id: int) -> None:
        zone = self.world.ruleset.get_zone(zone_id)
        player_spawn_spell_id, player_pos = zone.fetch_player()
        player_spawn_event = CombatEvent(self.event_id_gen.new_id(), self.world.timestamp, self.world.root_obj_id, player_spawn_spell_id, player_pos)
        self.current_events.append(player_spawn_event)
        enemy_spawn_spell_id, enemy_pos = zone.fetch_enemy()
        enemy_spawn_event = CombatEvent(self.event_id_gen.new_id(), self.world.timestamp, self.world.root_obj_id, enemy_spawn_spell_id, enemy_pos)
        self.current_events.append(enemy_spawn_event)
        self.process_combat()

    def read_player_input_events(self, combat_events: List[CombatEvent]) -> None:
        self.current_events.extend(combat_events)

    def update_aura_timers_and_create_aura_events(self, delta_time: float) -> None:
        self.world.delta_time = delta_time
        aura_ids: List[int] = sorted(self.world.auras.keys())
        for aura_id in aura_ids:
            aura = self.world.get_aura(aura_id)
            aura.update_timers(delta_time)
            if aura.try_process_tick():
                # Only process one aura tick per server tick
                self.add_event(aura.source_id, aura.spell_id, Dest(target_id=aura.target_id))

    def add_event(self, source_id: int, spell_id: int, dest: Dest) -> None:
        event = CombatEvent(self.event_id_gen.new_id(), self.world.timestamp, source_id, spell_id, dest)
        self.current_events.append(event)

    def get_player_obj(self) -> GameObj:
        for game_obj in self.world.game_objs.values():
            if game_obj.is_player is True:
                return game_obj
        return GameObj.create_empty()

    def process_combat(self) -> None:
        event_limit = 1000 # This failsafe should never be reached in-game
        while len(self.current_events) > 0 or event_limit <= 0:
            event_limit -= 1
            event = self.current_events.popleft()
            source_obj = self.world.get_game_obj(event.source_id)
            spell = self.world.ruleset.get_spell(event.spell_id)
            target_position = event.dest.copy()
            target_obj = source_obj
            if event.dest.has_target():
                target_obj = self.world.get_game_obj(event.dest.target_id)
            if not event.dest.has_target() and event.dest.has_position():
                # not yet implemented, but create new event on each target within position
                pass
            event.decide_outcome()
            is_disabled = self.world.aura_exists(spell.disabling_spell_id, source_obj.obj_id)
            if event.outcome == EventOutcome.SUCCESS and not is_disabled:
                if spell.has_cascade_spell():
                    self.add_event(source_obj.obj_id, spell.cascade_spell_id, target_obj)
                self._handle_special_spell_flags(source_obj, spell, target_obj, target_position)
                self._handle_spell_flags(source_obj, spell, target_obj, target_position)
            self.world.combat_event_log.add_event(event)

    def _handle_special_spell_flags(self, source_obj: GameObj, spell: Spell, target_obj: GameObj, pos: Dest) -> None:
        obj_to_receive_aura = target_obj
        if spell.has_npc_to_spawn():
            new_obj = GameObj(self.game_obj_id_gen.new_id(), pos)
            new_obj.load_npc_data(self.world.ruleset.get_npc(spell.spawn_npc_id))
            new_obj.parent_id = source_obj.obj_id
            self.world.add_game_obj(new_obj)
            obj_to_receive_aura = new_obj # Special rule for spawned NPCs
        if spell.has_aura_to_apply():
            aura_spell = self.world.ruleset.get_spell(spell.aura_spell_id)
            aura_dest = Dest(target_id=obj_to_receive_aura.obj_id)
            aura = Aura(self.game_obj_id_gen.new_id(), source_obj.obj_id, aura_spell, aura_dest.target_id)
            aura.apply_stack()

            self.world.game_objs[new_obj.obj_id] = new_obj
            self.world.auras[aura.aura_id] = aura

    def _handle_spell_flags(self, source_obj: GameObj, spell: Spell, target_obj: GameObj, pos: Dest) -> None:
        if spell.flags & SpellFlag.FIND_TARGET:
            for game_obj in self.world.game_objs.values():
                if game_obj.is_attackable and (game_obj.is_player != source_obj.is_player):
                    source_obj.destination.target_id = game_obj.obj_id
        if spell.flags & SpellFlag.MOVEMENT:
            direction = pos
            source_obj.position.move_in_direction(direction, target_obj.movement_speed, self.world.delta_time)
        if spell.flags & SpellFlag.DAMAGE:
            spell_power = spell.power * source_obj.get_spell_modifier()
            target_obj.suffer_damage(spell_power)
        if spell.flags & SpellFlag.HEAL:
            spell_power = spell.power * source_obj.get_spell_modifier()
            target_obj.restore_health(spell_power)


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

    def setup_game(self, zone_id: int) -> None:
        self.combat_handler.load_zone(zone_id)
        player_obj = self.combat_handler.get_player_obj()
        self.player_input_handler.set_player_obj(player_obj)

    def process_server_tick(self, delta_time: float, move_up: bool, move_left: bool, move_down: bool, move_right: bool, ability_1: bool, ability_2: bool, ability_3: bool, ability_4: bool) -> None:
        self.player_input_handler.update_input(delta_time, move_up, move_left, move_down, move_right, ability_1, ability_2, ability_3, ability_4)
        events_from_player = self.player_input_handler.fetch_combat_events()
        self.combat_handler.read_player_input_events(events_from_player)
        self.combat_handler.update_aura_timers_and_create_aura_events(delta_time)
        self.combat_handler.process_combat()

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
        self.npcs: List[Npc] = [
            Database.empty_npc(),
            Database.test_player(),
            Database.test_enemy(),
        ]
        self.spells: List[Spell] = [
            Database.empty_spell(),
            Database.player_movement(),
            Database.fireblast(),
            Database.blessed_aura(),
            Database.spawn_player(),
            Database.spawn_enemy(),
        ]
        self.zones: List[Zone] = [
            Database.empty_zone(),
            Database.test_zone(),
        ]

    # Npcs
    @staticmethod
    def empty_npc() -> Npc:
        return Npc(0)

    @staticmethod
    def test_player() -> Npc:
        npc = Npc(1)
        npc.hp = 30.0
        npc.is_player = True
        return npc

    @staticmethod
    def test_enemy() -> Npc:
        npc = Npc(2)
        npc.hp = 30.0
        npc.is_player = False
        return npc

    # Spells
    @staticmethod
    def empty_spell() -> Spell:
        return Spell(
            spell_id=0
        )

    @staticmethod
    def player_movement() -> Spell:
        return Spell(
            spell_id=1,
            flags=SpellFlag.MOVEMENT | SpellFlag.STOP_CAST
        )

    @staticmethod
    def fireblast() -> Spell:
        return Spell(
            spell_id=2,
            power=3.0,
            disabling_spell_id=Database.fireblast_cd().spell_id,
            flags=SpellFlag.DAMAGE | SpellFlag.FIND_TARGET
        )

    @staticmethod
    def fireblast_disabler() -> Spell:
        return Spell(
            spell_id=3,
            aura_spell_id=Database.blessed_aura().spell_id
        )

    @staticmethod
    def fireblast_cd() -> Spell:
        return Spell(
            spell_id=4,
            duration=2.0
        )

    @staticmethod
    def blessed_aura() -> Spell:
        return Spell(
            spell_id=5,
            duration=30.0,
            ticks=10,
            power=200.0,
            flags=SpellFlag.HEAL
        )

    @staticmethod
    def spawn_player() -> Spell:
        return Spell(
            spell_id=6,
            spawn_npc_id=Database.test_player().npc_id
        )

    @staticmethod
    def spawn_enemy() -> Spell:
        return Spell(
            spell_id=7,
            spawn_npc_id=Database.test_enemy().npc_id,
            aura_spell_id=Database.blessed_aura().spell_id
        )

    # Zones
    @staticmethod
    def empty_zone() -> Zone:
        return Zone(0)

    @staticmethod
    def test_zone() -> Zone:
        zone = Zone(1)
        zone.set_player(Database.spawn_player().spell_id, 0.3, 0.3)
        zone.set_enemy(Database.spawn_enemy().spell_id, 0.7, 0.7)
        return zone

#%%
if __name__ == "__main__":
    manager = GameManager()
    manager.simulate_game_in_console()