from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
from typing import Any, Dict, List, Tuple, Type, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json


class Color:
    """ Color configurations for drawing game objects. """
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    GREY: Tuple[int, int, int] = (128, 128, 128)
    RED: Tuple[int, int, int] = (255, 0, 0)
    GREEN: Tuple[int, int, int] = (0, 255, 0)
    BLUE: Tuple[int, int, int] = (0, 0, 255)


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


class SpellFlag(Flag):
    """ Flags for how spells should be handled. """
    NONE = 0
    MOVE_UP = auto()
    MOVE_LEFT = auto()
    MOVE_DOWN = auto()
    MOVE_RIGHT = auto()
    TELEPORT = auto()
    FIND_TARGET = auto()
    GCD = auto()
    DAMAGE = auto()
    HEAL = auto()
    DENY_IF_CASTING = auto()
    IS_CHANNEL = auto()
    WARP_TO_POSITION = auto()
    TRY_MOVE = auto()
    FORCE_MOVE = auto()
    SPAWN_NPC = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    AURA = auto()
    SLOT_1_ABILITY = auto()


class Spell(NamedTuple):
    """ An action that can be performed by a game object. """
    spell_id: int = IdGen.EMPTY_ID
    next_spell: int = IdGen.EMPTY_ID  # Next link in spell sequence (if this spell is part of one)

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


class Aura(NamedTuple):
    """ The effect of a spell that periodically ticks over a time span. """
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    target_id: int = IdGen.EMPTY_ID
    start_time: float = 0.0
    end_time: float = 0.0
    ticks: int = 1

    @classmethod
    def create_aura(cls, timestamp: float, source_id: int, spell: Spell, target_id: int) -> None:
        return Aura(
            source_id=source_id,
            spell_id=spell.spell_id,
            target_id=target_id,
            start_time=timestamp,
            end_time=timestamp + spell.duration,
            ticks=spell.ticks,
        )

    def get_aura_id(self) -> Tuple[int, int, int]:
        return self.source_id, self.spell_id, self.target_id

    def has_tick_this_frame(self, last_frame: float, now: float) -> bool:
        """ Ticks happen every tick_interval seconds, excluding t=start, including t=end. """
        if self.ticks == 0 or last_frame >= self.end_time or now <= self.start_time:
            return False
        tick_interval = self._get_tick_interval()
        ticks_elapsed = max(0, (last_frame - self.start_time) / tick_interval)
        next_tick = self.start_time + (math.ceil(ticks_elapsed) * tick_interval)
        return (last_frame < next_tick <= now) and (next_tick <= self.end_time)

    def _get_tick_interval(self) -> float:
        return float('inf') if self.ticks == 0 else self._get_duration() / self.ticks

    def _get_duration(self) -> float:
        return self.end_time - self.start_time


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = 1
    FAILED = 2
    MISSED = 3


class CombatEvent(NamedTuple):
    event_id: int = IdGen.EMPTY_ID
    parent_event: int = IdGen.EMPTY_ID
    timestamp: float = 0.0
    source: int = IdGen.EMPTY_ID
    spell: int = IdGen.EMPTY_ID
    dest: int = IdGen.EMPTY_ID  # Target object
    outcome: EventOutcome = EventOutcome.SUCCESS

    @classmethod
    def create_from_aura_tick(cls, event_id: int, timestamp: float, aura: Aura) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=aura.source_id,
            spell=aura.spell_id,
            dest=aura.target_id,
        )

    def get_event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] obj_{self.source:04d} uses spell_{self.spell:04d} on obj_{self.dest:04d}.)"

    def decide_outcome(self) -> None:
        #not implemented
        pass

    def is_aoe(self) -> bool:
        return False #fix later

    def is_spawn_event(self) -> bool:
        return IdGen.is_empty_id(self.source)

    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.dest)

    def continue_spell_sequence(self, new_event_id: int, new_spell_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, spell=new_spell_id)

    def also_target(self, new_event_id: int, new_target_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, dest=new_target_id)


class PlayerInput(NamedTuple):
    """ Keypresses for a given timestamp. Is used to make game objects cast spells. """
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


class GameObjStatus(Flag):
    """ Flags for various status effects of game objects. """
    NONE = 0
    CASTING = auto()
    CHANNELING = auto()
    STUNNED = auto()
    ATTACKABLE = auto()
    ALLIED = auto()
    BANISHED = auto()


@dataclass
class GameObj:
    """ Combat units. Controlled by the player or NPCs. """
    obj_id: Final[int] = IdGen.EMPTY_ID
    parent_id: Final[int] = IdGen.EMPTY_ID
    npc_id: Final[int] = IdGen.EMPTY_ID

    statuses: GameObjStatus = GameObjStatus.NONE

    # Targeting
    current_target: int = IdGen.EMPTY_ID
    selected_spell: int = IdGen.EMPTY_ID

    # Combat stats
    hp: float = 0.0
    movement_speed: float = 1.0
    is_attackable: bool = False
    is_player: bool = False

    # Positional data
    spawn_timestamp: float = 0.0
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    size: float = 0.0

    # Ability slots
    move_up_id: int = IdGen.EMPTY_ID
    move_left_id: int = IdGen.EMPTY_ID
    move_down_id: int = IdGen.EMPTY_ID
    move_right_id: int = IdGen.EMPTY_ID
    ability_1_id: int = IdGen.EMPTY_ID
    ability_2_id: int = IdGen.EMPTY_ID
    ability_3_id: int = IdGen.EMPTY_ID
    ability_4_id: int = IdGen.EMPTY_ID

    ability_1_cooldown: float = 0.0
    ability_2_cooldown: float = 0.0
    ability_3_cooldown: float = 0.0
    ability_4_cooldown: float = 0.0

    inputs: SortedDict[float, PlayerInput] = field(default_factory=SortedDict)
    auras: Dict[int, Aura] = field(default_factory=dict)

    @classmethod
    def embody_npc(cls, unique_obj_id: int, parent_id: int, other: 'GameObj') -> 'GameObj':
        new_obj: GameObj = other.copy()
        new_obj.obj_id = unique_obj_id
        new_obj.parent_id = parent_id
        return new_obj

    def fetch_events(self, event_id_gen: IdGen, t_previous: float, t_current: float) -> List[CombatEvent]:
        events: List[CombatEvent] = []
        for aura in self.auras.values():
            if aura.has_tick_this_frame(t_previous, t_current):
                assert aura.target_id == self.obj_id
                events.append(CombatEvent.create_from_aura_tick(event_id_gen.new_id(), t_current, aura))
        for timestamp in self.inputs.irange(t_previous-self.spawn_timestamp, t_current-self.spawn_timestamp, inclusive=(False, True)):
            player_input: PlayerInput = self.inputs[timestamp]
            events += InputHandler.convert_to_events(event_id_gen, t_current, self, player_input)
        return events

    def add_input(self, timestamp: float, new_input: PlayerInput) -> None:
        assert timestamp not in self.inputs, \
            f"Input for timestamp={timestamp} already exists in obj_id={self.obj_id}"
        self.inputs[timestamp] = new_input

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

    def teleport_to(self, new_x: float, new_y: float) -> None:
        self.x = new_x
        self.y = new_y

    def move_in_direction(self, x: float, y: float, move_speed: float, delta_t: float) -> None:
        self.x += x * move_speed * delta_t
        self.y += y * move_speed * delta_t

    def suffer_damage(self, spell_power: float) -> None:
        self.hp -= spell_power

    def restore_health(self, spell_power: float) -> None:
        self.hp += spell_power


class Ruleset:
    """ Static game configuration that should not be changed after combat has started. """
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
    """ A collection of logs for all combat events that have occurred. """
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

        self.event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self.game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self.environment: GameObj = GameObj(obj_id=self.game_obj_id_gen.new_id())
        self.boss: Optional[GameObj] = None
        self.player: Optional[GameObj] = None

        self.ruleset: Ruleset = Ruleset()
        self.auras: Dict[Tuple[int, int, int], Aura] = {}
        self.game_objs: Dict[int, GameObj] = {self.environment.obj_id: self.environment}
        self.combat_event_log: EventLog = EventLog()

    def setup_game_obj(self, setup_spell_id: int) -> None:
        setup_event = CombatEvent(
            event_id=self.event_id_gen.new_id(),
            timestamp=self.current_timestamp,
            source=self.environment.obj_id,
            spell=setup_spell_id,
        )
        self._handle_event(setup_event)

    def advance_combat(self, delta_time: float, player_input: PlayerInput) -> None:
        self.previous_timestamp = self.current_timestamp
        self.current_timestamp += delta_time
        if self.player is not None:
            self.player.add_input(self.current_timestamp, player_input)
        events: List[CombatEvent] = []
        for obj in self.game_objs.values():
            events += obj.fetch_events(self.event_id_gen, self.previous_timestamp, self.current_timestamp)
        for event in events:
            self._handle_event(event)

    def _handle_event(self, event: CombatEvent) -> None:
        source_obj = self.get_game_obj(event.source)
        spell = self.ruleset.get_spell(event.spell)
        target_obj = source_obj
        if not IdGen.is_empty_id(event.dest):
            target_obj = self.get_game_obj(event.dest)
        event.decide_outcome()
        if event.outcome == EventOutcome.SUCCESS:
            if not IdGen.is_empty_id(spell.next_spell):
                new_event = event.continue_spell_sequence(self.event_id_gen.new_id(), spell.next_spell)
                self._handle_event(new_event)
            SpellHandler.handle_spell(source_obj, spell, target_obj, self)
        self.combat_event_log.add_event(event)

    def add_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self.game_objs, f"Game object with ID {game_obj.obj_id} already exists."
        self.game_objs[game_obj.obj_id] = game_obj

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self.game_objs, f"Game object with ID {obj_id} does not exist."
        return self.game_objs.get(obj_id, GameObj())

    def get_delta_time(self) -> float:
        return self.current_timestamp - self.previous_timestamp


class SpellHandler:
    @staticmethod
    def handle_spell(source_obj: GameObj, spell: Spell, target_obj: GameObj, world: World) -> None:
        if spell.flags & SpellFlag.SPAWN_NPC or spell.flags & SpellFlag.SPAWN_PLAYER or spell.flags & SpellFlag.SPAWN_PLAYER:
            obj_id = world.game_obj_id_gen.new_id()
            npc_template = world.ruleset.get_npc(spell.spell_id)
            new_obj = GameObj.embody_npc(obj_id, source_obj.obj_id, npc_template)
            world.add_game_obj(new_obj)
            if spell.flags & SpellFlag.SPAWN_BOSS:
                world.boss = new_obj
            if spell.flags & SpellFlag.SPAWN_PLAYER:
                world.player = new_obj
        if spell.flags & SpellFlag.AURA:
            aura_spell = world.ruleset.get_spell(spell.next_spell)
            aura = Aura.create_aura(world.current_timestamp, source_obj.obj_id, aura_spell, target_obj.obj_id)
            target_obj.add_aura(aura)

        # Handle spell flags
        if spell.flags & SpellFlag.FIND_TARGET:
            for game_obj in world.game_objs.values():
                if game_obj.statuses & GameObjStatus.ALLIED != source_obj.statuses & GameObjStatus.ALLIED:
                    source_obj.target_id = game_obj.obj_id
        if spell.flags & SpellFlag.MOVE_UP:
            source_obj.move_in_direction(0.0, 1.0, target_obj.movement_speed, world.get_delta_time())
        if spell.flags & SpellFlag.MOVE_LEFT:
            source_obj.move_in_direction(-1.0, 0.0, target_obj.movement_speed, world.get_delta_time())
        if spell.flags & SpellFlag.MOVE_DOWN:
            source_obj.move_in_direction(0.0, -1.0, target_obj.movement_speed, world.get_delta_time())
        if spell.flags & SpellFlag.MOVE_RIGHT:
            source_obj.move_in_direction(1.0, 0.0, target_obj.movement_speed, world.get_delta_time())
        if spell.flags & SpellFlag.DAMAGE:
            spell_power = spell.power * source_obj.get_spell_modifier()
            target_obj.suffer_damage(spell_power)
        if spell.flags & SpellFlag.HEAL:
            spell_power = spell.power * source_obj.get_spell_modifier()
            target_obj.restore_health(spell_power)


class SpellValidator:
    @staticmethod
    def validate_spell(source_obj: GameObj, spell: Spell, target_obj: GameObj, world: World) -> EventOutcome:
        if spell.flags & (SpellFlag.MOVE_UP | SpellFlag.MOVE_LEFT | SpellFlag.MOVE_DOWN | SpellFlag.MOVE_RIGHT):
            return EventOutcome.SUCCESS

class InputHandler:

    @staticmethod
    def convert_to_events(id_gen: IdGen, timestamp: float, obj: GameObj, game_input: PlayerInput) -> List[CombatEvent]:
        spell_ids: List[int] = []
        spell_ids += [obj.move_up_id] if game_input.move_up else []
        spell_ids += [obj.move_left_id] if game_input.move_left else []
        spell_ids += [obj.move_down_id] if game_input.move_down else []
        spell_ids += [obj.move_right_id] if game_input.move_right else []
        spell_ids += [obj.ability_1_id] if game_input.ability_1 else []
        spell_ids += [obj.ability_2_id] if game_input.ability_2 else []
        spell_ids += [obj.ability_3_id] if game_input.ability_3 else []
        spell_ids += [obj.ability_4_id] if game_input.ability_4 else []
        assert IdGen.EMPTY_ID not in spell_ids
        events: List[CombatEvent] = []
        for spell_id in spell_ids:
            events.append(CombatEvent(
                event_id=id_gen.new_id(),
                timestamp=timestamp,
                source=obj.obj_id,
                spell=spell_id,
                dest=obj.current_target,
            ))
        return events


class GameManager:
    def __init__(self) -> None:
        self.world: World = World()

    def simulate_game_in_console(self) -> None:
        self.setup_game(1)
        SIMULATION_DURATION = 5
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of player input
            self.process_server_tick(1 / UPDATES_PER_SECOND, True, False, False, False, True, False, False, False)

    def setup_game(self, setup_spell_id: int) -> None:
        self.world.setup_game_obj(setup_spell_id)

    def process_server_tick(self, delta_time: float, move_up: bool, move_left: bool, move_down: bool, move_right: bool, ability_1: bool, ability_2: bool, ability_3: bool, ability_4: bool) -> None:
        self.world.advance_combat(delta_time, PlayerInput(local_timestamp=self.world.current_timestamp, move_up=move_up, move_left=move_left, move_down=move_down, move_right=move_right, ability_1=ability_1, ability_2=ability_2, ability_3=ability_3, ability_4=ability_4))

    def get_all_game_objs_to_draw(self) -> List[GameObj]:
        return self.world.game_objs.values()


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


class Utils:

    @staticmethod
    def load_collection(class_with_methods: Type[Any]) -> List[Any]:
        static_methods = [name for name, attr in class_with_methods.__dict__.items() if isinstance(attr, staticmethod)]
        return [getattr(class_with_methods, method)() for method in static_methods]

class Database:
    def __init__(self) -> None:
        self.spells: List[Spell] = Database.load_spell_collections()
        self.npcs: List[GameObj] = Database.load_npc_collections()

    @staticmethod
    def load_spell_collections() -> List[Spell]:
        spells: List[Spell] = []
        spells += Utils.load_collection(SpellCollectionCore)
        return spells

    @staticmethod
    def load_npc_collections() -> List[GameObj]:
        npcs: List[GameObj] = []
        npcs += Utils.load_collection(NpcCollectionCore)
        return npcs



class SpellCollectionCore:
    @staticmethod
    def empty_spell() -> Spell:
        return Spell(spell_id=0)

    @staticmethod
    def player_move_up() -> Spell:
        return Spell(spell_id=1, flags=SpellFlag.MOVE_UP | SpellFlag.DENY_IF_CASTING)
    @staticmethod
    def player_move_left() -> Spell:
        return Spell(spell_id=2, flags=SpellFlag.MOVE_LEFT | SpellFlag.DENY_IF_CASTING)
    @staticmethod
    def player_move_down() -> Spell:
        return Spell(spell_id=3, flags=SpellFlag.MOVE_DOWN | SpellFlag.DENY_IF_CASTING)
    @staticmethod
    def player_move_right() -> Spell:
        return Spell(spell_id=4, flags=SpellFlag.MOVE_RIGHT | SpellFlag.DENY_IF_CASTING)

    @staticmethod
    def fireblast() -> Spell:
        return Spell(
            spell_id=5,
            power=3.0,
            flags=SpellFlag.DAMAGE | SpellFlag.FIND_TARGET,
        )

    @staticmethod
    def humble_heal() -> Spell:
        return Spell(
            spell_id=6,
            duration=30.0,
            ticks=50,
            power=200.0,
            flags=SpellFlag.HEAL,
        )

    @staticmethod
    def blessed_aura() -> Spell:
        return Spell(
            spell_id=7,
            next_spell=SpellCollectionCore.humble_heal().spell_id,
            flags=SpellFlag.AURA,
        )

    @staticmethod
    def spawn_player() -> Spell:
        return Spell(
            spell_id=8,
            next_spell=SpellCollectionCore.spawn_enemy().spell_id,
            flags=SpellFlag.SPAWN_PLAYER,
        )

    @staticmethod
    def spawn_enemy() -> Spell:
        return Spell(
            spell_id=9,
            flags=SpellFlag.SPAWN_NPC,
        )

    @staticmethod
    def setup_test_zone() -> Spell:
        return Spell(
            spell_id=10,
            next_spell=SpellCollectionCore.spawn_player().spell_id,
        )


class NpcCollectionCore:
    @staticmethod
    def empty_npc() -> GameObj:
        return GameObj(
            npc_id=0,
        )

    @staticmethod
    def test_player() -> GameObj:
        return GameObj(
            npc_id=SpellCollectionCore.spawn_player().spell_id,
            hp=30.0,
            statuses=GameObjStatus.ALLIED,
            x=0.3,
            y=0.3,
            move_up_id=SpellCollectionCore.player_move_up().spell_id,
            move_left_id=SpellCollectionCore.player_move_left().spell_id,
            move_down_id=SpellCollectionCore.player_move_down().spell_id,
            move_right_id=SpellCollectionCore.player_move_right().spell_id,
            ability_1_id=SpellCollectionCore.fireblast().spell_id,
            ability_2_id=SpellCollectionCore.fireblast().spell_id,
            ability_3_id=SpellCollectionCore.fireblast().spell_id,
            ability_4_id=SpellCollectionCore.fireblast().spell_id,
        )

    @staticmethod
    def test_enemy() -> GameObj:
        game_inputs: SortedDict[float, PlayerInput] = SortedDict()
        input_1 = PlayerInput(local_timestamp=3.0, ability_1=True)
        input_2 = PlayerInput(local_timestamp=5.0, ability_2=True)
        game_inputs[input_1.local_timestamp] = input_1
        game_inputs[input_2.local_timestamp] = input_2
        return GameObj(
            npc_id=SpellCollectionCore.spawn_enemy().spell_id,
            hp=30.0,
            x=0.7,
            y=0.7,
            ability_1_id=SpellCollectionCore.humble_heal().spell_id,
            ability_2_id=SpellCollectionCore.blessed_aura().spell_id,
            inputs=game_inputs,
        )


#%%
if __name__ == "__main__":
    manager = GameManager()
    manager.simulate_game_in_console()