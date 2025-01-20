from typing import Dict, Set, List, Any, Deque, Tuple, Final, Optional
from collections import deque
from enum import Enum, Flag, auto
import math
import json
from copy import copy, deepcopy

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
    SPAWN_NPC = auto()
    FIND_TARGET = auto()
    DAMAGE = auto()
    HEAL = auto()
    IS_CHANNEL = auto()
    WARP_TO_POSITION = auto()
    TRY_MOVE = auto()
    FORCE_MOVE = auto()


class Spell:
    def __init__(self, spell_id: int) -> None:
        self.spell_id: Final[int] = spell_id
        self.spawn_npc_id: int = IdGenerator.EMPTY_ID

        self.setup_spell_id: int = IdGenerator.EMPTY_ID
        self.finish_spell_id: int = IdGenerator.EMPTY_ID

        self.power: float = 0
        self.variance: float = 0

        self.range_limit: float = 0
        self.cost: float = 0
        self.cast_time: float = 0
        self.duration: float = 0
        self.ticks: int = 0
        self.cooldown: float = 0
        self.max_stacks: int = 0
        self.gcd_mod: float = 0

        self.flags: SpellFlag = SpellFlag.NONE

    @classmethod
    def create_empty(cls) -> 'Spell':
        return Spell(IdGenerator.EMPTY_ID)
    @classmethod
    def from_json(cls, json_str: str) -> 'Spell':
        return cls(**{k: v for k, v in json.loads(json_str).items() if k in cls.__init__.__code__.co_varnames})
    def to_json(self) -> str:
        return json.dumps({key: value for key, value in self.__dict__.items() if value != Spell.create_empty().__dict__[key]})
    def copy(self) -> 'Spell':
        return copy(self)
    def is_equal(self, other) -> bool:
        if not isinstance(other, Spell):
            return False
        return self.__dict__ == other.__dict__

    def has_pre_spell(self) -> bool:
        return self.setup_spell_id != IdGenerator.EMPTY_ID

    def has_post_spell(self) -> bool:
        return self.finish_spell_id != IdGenerator.EMPTY_ID

class Aura:
    def __init__(self, aura_id: int, source_id: int, target_id: int, spell: Spell) -> None:
        self.aura_id: Final[int] = aura_id
        self.source_id: Final[int] = source_id
        self.target_id: Final[int] = target_id
        self.spell_id: Final[int] = spell.spell_id
        self.spell_duration: Final[float] = spell.duration
        self.spell_max_stacks: Final[int] = spell.max_stacks
        self.spell_ticks: Final[int] = spell.ticks

        self.activation_delay: float = 0.0
        self.time_remaining: float = 0.0
        self.stacks: int = 0
        self.tick_interval: float = 0.0
        self.time_since_last_tick: float = 0.0
        self.ticks_awaiting_processing: int = 0

    @classmethod
    def create_empty(cls) -> 'Aura':
        return Aura(IdGenerator.EMPTY_ID, IdGenerator.EMPTY_ID, IdGenerator.EMPTY_ID, Spell.create_empty())
    @classmethod
    def from_json(cls, json_str: str) -> 'Aura':
        data = json.loads(json_str)
        temp_spell = Spell(data['spell_id'])
        temp_spell.duration = data['spell_duration']
        temp_spell.max_stacks = data['spell_max_stacks']
        temp_spell.ticks = data['spell_ticks']
        aura = cls(data['aura_id'], data['source_id'], data['target_id'], temp_spell)
        aura.activation_delay = data['activation_delay']
        aura.time_remaining = data['time_remaining']
        aura.stacks = data['stacks']
        aura.tick_interval = data['tick_interval']
        aura.time_since_last_tick = data['time_since_last_tick']
        aura.ticks_awaiting_processing = data['ticks_awaiting_processing']
        return aura
    def to_json(self) -> str:
        return json.dumps(self.__dict__)
    def is_equal(self, other) -> bool:
        if not isinstance(other, Aura):
            return False
        return self.__dict__ == other.__dict__
    def copy(self) -> 'Aura':
        return copy(self)
    def is_empty(self) -> bool:
        return self.aura_id == IdGenerator.EMPTY_ID

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
        self.time_since_last_tick += delta_time
        if self.time_since_last_tick >= self.tick_interval:
            self.time_since_last_tick -= self.tick_interval
            self.ticks_awaiting_processing += 1
        self.time_remaining -= delta_time
        if self.time_remaining <= 0.0:
            self.stacks = 0
            self.time_remaining = 0.0
            self.tick_interval = 0.0
            self.time_since_last_tick = 0.0

    def try_process_tick(self) -> bool:
        if self.ticks_awaiting_processing > 0:
            self.ticks_awaiting_processing -= 1
            return True
        return False

class Pos:
    def __init__(self) -> None:
        self.zone_id: int = 0
        self.local_time: float = 0.0
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
        self.ignore_pos: bool = False

    @classmethod
    def create_empty(cls) -> 'Pos':
        return Pos()
    @classmethod
    def create_at(cls, zone_id: int, pos_x: float, pos_y: float) -> 'Pos':
        pos = Pos()
        pos.zone_id = zone_id
        pos.pos_x = pos_x
        pos.pos_y = pos_y
        return pos
    def copy(self) -> 'Pos':
        return copy(self)

    def move_in_direction(self, direction: 'Pos', movement_speed: float, delta_time: float) -> None:
        self.pos_x += direction.pos_x * movement_speed * delta_time
        self.pos_y += direction.pos_y * movement_speed * delta_time


class Dest:
    def __init__(self, target_obj_id: int, target_position: Pos) -> None:
        self.target_obj_id: int = target_obj_id
        self.target_position: Pos = target_position

    @classmethod
    def create_empty(cls) -> 'Dest':
        return Dest(IdGenerator.EMPTY_ID, Pos.create_empty())

    @classmethod
    def create_positional(cls, target_position: Pos) -> 'Dest':
        return Dest(IdGenerator.EMPTY_ID, target_position)

    @classmethod
    def create_targeted(cls, target_obj_id) -> 'Dest':
        return Dest(target_obj_id, Pos.create_empty())

    def copy(self) -> 'Dest':
        return Dest(self.target_obj_id, self.target_position.copy())

class Npc:
    def __init__(self, npc_id: int) -> None:
        self.npc_id: Final[int] = npc_id
        self.spawn_spell_id: int = 0
        self.hp: float = 0.0
        self.movement_speed: float = 1.0
        self.is_attackable: bool = False
        self.is_player: bool = False

    @classmethod
    def create_empty(cls) -> 'Npc':
        return Npc(IdGenerator.EMPTY_ID)

    def is_empty(self) -> bool:
        return self.npc_id == IdGenerator.EMPTY_ID

    def has_spawn_spell(self) -> bool:
        return self.spawn_spell_id != IdGenerator.EMPTY_ID


class GameObj:
    def __init__(self, obj_id: int, position: Pos) -> None:
        self.obj_id: Final[int] = obj_id
        self.parent_id: int = IdGenerator.EMPTY_ID
        self.npc_properties: Npc = Npc.create_empty()
        self.position: Pos = position
        self.destination: Dest = Dest.create_empty()
        self.hp: float = 0.0
        self.movement_speed: float = 1.0
        self.is_attackable: bool = False
        self.is_player: bool = False

    @classmethod
    def create_empty(cls) -> 'GameObj':
        return GameObj(IdGenerator.EMPTY_ID, Pos.create_empty())

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

    def teleport_to(self, new_position: Pos) -> None:
        self.position.pos_x = new_position.pos_x
        self.position.pos_y = new_position.pos_y

    def suffer_damage(self, spell_power: float) -> None:
        self.hp -= spell_power


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
        self.dest: Dest = dest
        self.outcome: EventOutcome = EventOutcome.EMPTY


    @classmethod
    def create_empty(cls) -> 'CombatEvent':
        return CombatEvent(IdGenerator.EMPTY_ID, 0.0, IdGenerator.EMPTY_ID, IdGenerator.EMPTY_ID, Dest.create_empty())

    def is_empty(self) -> bool:
        return self.event_id == IdGenerator.EMPTY_ID

    def get_event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] obj_{self.source_id:04d} uses spell_{self.spell_id:04d} on obj_{self.dest.target_obj_id:04d} at (x={self.dest.target_position.pos_x:.3f}, y={self.dest.target_position.pos_y:.3f})"

    def decide_outcome(self) -> None:
        #not implemented
        self.outcome = EventOutcome.SUCCESS


class Zone:
    def __init__(self, zone_id: int) -> None:
        self.zone_id: Final[int] = zone_id
        self.player_spawn: Tuple[int, Pos] = (IdGenerator.EMPTY_ID, Pos.create_empty())
        self.enemy_spawns: List[Tuple[int, Pos]] = []

    @classmethod
    def create_empty(cls) -> 'Zone':
        return Zone(IdGenerator.EMPTY_ID)

    def is_empty(self) -> bool:
        return self.zone_id == IdGenerator.EMPTY_ID

    def fetch_player(self) -> Tuple[int, Pos]:
        return (self.player_spawn[0], self.player_spawn[1].copy())

    def fetch_enemies(self) -> List[Tuple[int, Pos]]:
        enemies_copy = []
        for element in self.enemy_spawns:
            enemies_copy.append((element[0], element[1].copy()))
        return enemies_copy

    def set_player(self, spell_id: int, pos_x: float, pos_y: float) -> None:
        self.player_spawn = (spell_id, Pos.create_at(self.zone_id, pos_x, pos_y))

    def set_enemy(self, spell_id: int, pos_x: float, pos_y: float) -> None:
        self.enemy_spawns.append((spell_id, Pos.create_at(self.zone_id, pos_x, pos_y)))


class Ruleset:
    def __init__(self) -> None:
        self.npcs: Dict[int, Npc] = {}
        self.spells: Dict[int, Spell] = {}
        self.zones: Dict[int, Zone] = {}
        self.populate_ruleset()

    def get_npc(self, npc_id: int) -> Npc:
        assert npc_id in self.npcs
        return self.npcs.get(npc_id, Npc.create_empty())

    def add_npc(self, npc: Npc) -> None:
        assert npc.npc_id not in self.npcs
        self.npcs[npc.npc_id] = npc

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells
        return self.spells.get(spell_id, Spell.create_empty())

    def add_spell(self, spell: Spell) -> None:
        assert spell.spell_id not in self.spells
        self.spells[spell.spell_id] = spell

    def get_zone(self, zone_id: int) -> Zone:
        assert zone_id in self.zones
        return self.zones.get(zone_id, Zone.create_empty())

    def add_zone(self, zone: Zone) -> None:
        assert zone.zone_id not in self.zones
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
        world.add_game_obj(GameObj(root_obj_id, Pos.create_empty()))
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
        if not self._assigned_ids:
            assert self._assigned_ids
            return IdGenerator.EMPTY_ID
        return self._assigned_ids.popleft()

    def reserve_id(self, reserved_id: int) -> None:
        self._reserved_ids.add(reserved_id)
        self._assigned_ids = deque(id_num for id_num in self._assigned_ids if id_num != reserved_id)


class PlayerInputHandler:
    def __init__(self) -> None:
        self.event_id_gen: IdGenerator = IdGenerator(1000, 10_000)
        self.combat_events: List[CombatEvent] = []
        self.player_obj: GameObj = GameObj.create_empty()
        self.movement_spell_id: int = Database.player_movement().spell_id #hardcoded for now
        self.ability_1_spell_id: int = Database.test_st_insta().spell_id #hardcoded for now
        self.ability_2_spell_id: int = Database.test_st_insta().spell_id #hardcoded for now
        self.ability_3_spell_id: int = Database.test_st_insta().spell_id #hardcoded for now
        self.ability_4_spell_id: int = Database.test_st_insta().spell_id #hardcoded for now
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
            pos = Pos()
            if self.is_pressing_move_up:
                pos.pos_y += 1.0
            if self.is_pressing_move_left:
                pos.pos_x -= 1.0
            if self.is_pressing_move_down:
                pos.pos_y -= 1.0
            if self.is_pressing_move_right:
                pos.pos_x += 1.0
            self._create_event(self.movement_spell_id, Dest.create_positional(pos))
        target_id = self.player_obj.destination.target_obj_id
        if self.is_pressing_ability_1:
            self._create_event(self.ability_1_spell_id, Dest.create_targeted(target_id))
        if self.is_pressing_ability_2:
            self._create_event(self.ability_2_spell_id, Dest.create_targeted(target_id))
        if self.is_pressing_ability_3:
            self._create_event(self.ability_3_spell_id, Dest.create_targeted(target_id))
        if self.is_pressing_ability_4:
            self._create_event(self.ability_4_spell_id, Dest.create_targeted(target_id))


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
        self.aura_id_gen: IdGenerator = IdGenerator(1, 10_000)
        self.event_id_gen: IdGenerator = IdGenerator(1, 1000)
        self.game_obj_id_gen: IdGenerator = IdGenerator(1, 10_000)
        self.world: World = World.create_with_root_obj(self.game_obj_id_gen.new_id())
        self.current_events: Deque[CombatEvent] = deque()

    def load_zone(self, zone_id: int) -> None:
        zone = self.world.ruleset.get_zone(zone_id)
        player_spawn_spell_id, player_pos = zone.fetch_player()
        player_spawn_event = CombatEvent(self.event_id_gen.new_id(), self.world.timestamp, self.world.root_obj_id, player_spawn_spell_id, Dest.create_positional(player_pos))
        self.current_events.append(player_spawn_event)
        for enemy_spawn_spell_id, enemy_pos in zone.fetch_enemies():
            enemy_spawn_event = CombatEvent(self.event_id_gen.new_id(), self.world.timestamp, self.world.root_obj_id, enemy_spawn_spell_id, Dest.create_positional(enemy_pos))
            self.current_events.append(enemy_spawn_event)
        self.process_combat()

    def update_aura_timers_and_create_aura_events(self, delta_time: float) -> None:
        self.world.delta_time = delta_time
        aura_ids: List[int] = sorted(self.world.auras.keys())
        for aura_id in aura_ids:
            aura = self.world.get_aura(aura_id)
            aura.update_timers(delta_time)
            if aura.try_process_tick():
                dest = Dest(aura.target_id, self.world.get_game_obj(aura.target_id).position)
                self.create_events_for_spell(aura.source_id, aura.spell_id, dest)

    def read_player_input_events(self, combat_events: List[CombatEvent]) -> None:
        self.current_events.extend(combat_events)

    def create_events_for_spell(self, source_id: int, spell_id: int, dest: Dest) -> None:
        spell = self.world.ruleset.get_spell(spell_id)
        # pre-spell recursive call
        if spell.has_pre_spell():
            self.create_events_for_spell(source_id, spell.setup_spell_id, dest)
        # main spell
        event = CombatEvent(self.event_id_gen.new_id(), self.world.timestamp, source_id, spell.spell_id, dest)
        self.current_events.append(event)
        # post-spell recursive call
        if spell.has_post_spell():
            self.create_events_for_spell(source_id, spell.finish_spell_id, dest)

    def process_combat(self) -> None:
        event_limit = 1000 #this is a failsafe that preferably should never be reached
        while len(self.current_events) > 0 or event_limit <= 0:
            event_limit -= 1
            event = self.current_events.popleft()
            source_obj = self.world.get_game_obj(event.source_id)
            spell = self.world.ruleset.get_spell(event.spell_id)
            target_obj = source_obj
            if event.dest.target_obj_id != IdGenerator.EMPTY_ID:
                target_obj = self.world.get_game_obj(event.dest.target_obj_id)
            event.decide_outcome()
            if event.outcome == EventOutcome.SUCCESS:
                if spell.flags & SpellFlag.SPAWN_NPC:
                    new_obj = GameObj(self.game_obj_id_gen.new_id(), event.dest.target_position.copy())
                    new_obj.load_npc_data(self.world.ruleset.get_npc(spell.spawn_npc_id))
                    self.world.add_game_obj(new_obj)
                    if new_obj.npc_properties.has_spawn_spell():
                        npc_spell = self.world.ruleset.get_spell(new_obj.npc_properties.spawn_spell_id)
                        aura = Aura(self.game_obj_id_gen.new_id(), new_obj.obj_id, new_obj.obj_id, npc_spell)
                        self.world.game_objs[new_obj.obj_id] = new_obj
                        self.world.auras[aura.aura_id] = aura
                if spell.flags & SpellFlag.MOVEMENT:
                    direction = event.dest.target_position.copy()
                    print(f"{direction.pos_x}, {direction.pos_y}")
                    source_obj.position.move_in_direction(direction, target_obj.movement_speed, self.world.delta_time)
                if spell.flags & SpellFlag.DAMAGE:
                    spell_power = spell.power * source_obj.get_spell_modifier()
                    target_obj.suffer_damage(spell_power)
                if spell.flags & SpellFlag.FIND_TARGET:
                    for game_obj in self.world.game_objs.values():
                        if game_obj.is_attackable and (game_obj.is_player != source_obj.is_player):
                            source_obj.destination.target_obj_id = game_obj.obj_id
            self.world.combat_event_log.add_event(event)

    def get_player_obj(self) -> GameObj:
        for game_obj in self.world.game_objs.values():
            if game_obj.is_player is True:
                return game_obj
        return GameObj.create_empty()


class GameManager:
    def __init__(self) -> None:
        self.combat_handler: CombatHandler = CombatHandler()
        self.player_input_handler: PlayerInputHandler = PlayerInputHandler()

    def simulate_game_in_console(self) -> None:
        self.setup_game(1)
        SIMULATION_DURATION = 2
        UPDATES_PER_SECOND = 5
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
            Database.test_st_insta(),
            Database.target_swap(),
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
        return Spell(0)

    @staticmethod
    def player_movement() -> Spell:
        spell = Spell(1)
        spell.flags = SpellFlag.MOVEMENT
        return spell

    @staticmethod
    def test_st_insta() -> Spell:
        spell = Spell(2)
        spell.range_limit = 99999.0
        spell.power = 1.5
        spell.flags = SpellFlag.DAMAGE
        return spell

    @staticmethod
    def target_swap() -> Spell:
        spell = Spell(3)
        spell.flags = SpellFlag.FIND_TARGET
        return spell

    @staticmethod
    def spawn_player() -> Spell:
        spell = Spell(4)
        spell.spawn_npc_id = Database.test_player().npc_id
        spell.flags = SpellFlag.SPAWN_NPC
        return spell

    @staticmethod
    def spawn_enemy() -> Spell:
        spell = Spell(5)
        spell.spawn_npc_id = Database.test_enemy().npc_id
        spell.flags = SpellFlag.SPAWN_NPC
        return spell

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