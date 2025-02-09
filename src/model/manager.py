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
    SELF_CAST = auto()
    TAB_TARGET = auto()
    TELEPORT = auto()
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
    alias_id: int = IdGen.EMPTY_ID
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

    @property
    def template_id(self) -> int:
        if IdGen.is_empty_id(self.alias_id):
            return self.spell_id
        return self.alias_id

    @property
    def is_spell_sequence(self) -> bool:
        return not IdGen.is_empty_id(self.next_spell)


class Aura(NamedTuple):
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    target_id: int = IdGen.EMPTY_ID
    start_time: float = 0.0
    end_time: float = 0.0
    ticks: int = 1
    is_debuff: bool = False
    is_hidden: bool = False

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

    @property
    def aura_id(self) -> Tuple[int, int, int]:
        return self.source_id, self.spell_id, self.target_id

    def has_tick_this_frame(self, last_frame: float, now: float) -> bool:
        """ Ticks happen every tick_interval seconds, excluding t=start, including t=end. """
        if self.ticks == 0 or last_frame >= self.end_time or now <= self.start_time:
            return False
        tick_interval = self._tick_interval
        ticks_elapsed = max(0, (last_frame - self.start_time) / tick_interval)
        next_tick = self.start_time + (math.ceil(ticks_elapsed) * tick_interval)
        return (last_frame < next_tick <= now) and (next_tick <= self.end_time)

    @property
    def _tick_interval(self) -> float:
        return float('inf') if self.ticks == 0 else self._duration / self.ticks

    @property
    def _duration(self) -> float:
        return self.end_time - self.start_time


class PlayerInput(NamedTuple):
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


class EventTrigger(Enum):
    EMPTY = 0
    PLAYER_INPUT = 1
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
    trigger: EventTrigger = EventTrigger.EMPTY
    source: int = IdGen.EMPTY_ID
    spell: int = IdGen.EMPTY_ID
    target: int = IdGen.EMPTY_ID  # Target object
    outcome: EventOutcome = EventOutcome.EMPTY

    @classmethod
    def create_from_aura_tick(cls, event_id: int, timestamp: float, aura: Aura) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            trigger=EventTrigger.AURA_TICK,
            source=aura.source_id,
            spell=aura.spell_id,
            target=aura.target_id,
        )

    @classmethod
    def create_from_input(cls, event_id: int, timestamp: float, source_id: int, spell_id: int, target_id: int) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            trigger=EventTrigger.PLAYER_INPUT,
            source=source_id,
            spell=spell_id,
            target=target_id,
        )

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] obj_{self.source:04d} uses spell_{self.spell:04d} on obj_{self.target:04d}.)"

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
        return self._replace(event_id=new_event_id, dest=new_target_id)


class GameObjStatus(Flag):
    """ Flags for various status effects of game objects. """
    NONE = 0
    CASTING = auto()
    CHANNELING = auto()
    STUNNED = auto()
    ATTACKABLE = auto()
    BANISHED = auto()


@dataclass
class GameObj:
    """ Combat units. Controlled by the player or NPCs. """
    obj_id: Final[int] = IdGen.EMPTY_ID
    parent_id: Final[int] = IdGen.EMPTY_ID
    template_id: Final[int] = IdGen.EMPTY_ID

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

    # Positional data
    spawn_timestamp: float = 0.0
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

    ability_1_cooldown: float = 0.0
    ability_2_cooldown: float = 0.0
    ability_3_cooldown: float = 0.0
    ability_4_cooldown: float = 0.0

    inputs: SortedDict[float, PlayerInput] = field(default_factory=SortedDict)
    auras: Dict[int, Aura] = field(default_factory=dict)

    @property
    def size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.hp))

    @property
    def spell_modifier(self) -> float:
        #calculation not yet implemented
        return 1.0

    @classmethod
    def create_from_template(cls, unique_obj_id: int, parent_id: int, other: 'GameObj') -> 'GameObj':
        new_obj: GameObj = other.copy()
        new_obj.obj_id = unique_obj_id
        new_obj.parent_id = parent_id
        return new_obj

    def fetch_events(self, event_id_gen: IdGen, t_previous: float, t_current: float) -> List[CombatEvent]:
        events: List[CombatEvent] = []
        for aura in self.auras.values():
            if aura.has_tick_this_frame(t_previous, t_current):
                assert aura.target_id == self.obj_id, f"Aura sitting on {self.obj_id} is targeting {aura.target_id}."
                events.append(CombatEvent.create_from_aura_tick(event_id_gen.new_id(), t_current, aura))
        for timestamp in self.inputs.irange(t_previous-self.spawn_timestamp, t_current-self.spawn_timestamp, inclusive=(False, True)):
            player_input: PlayerInput = self.inputs[timestamp]
            events += InputHandler.convert_to_events(event_id_gen, t_current, self, player_input)
        return events

    def add_input(self, timestamp: float, new_input: PlayerInput) -> None:
        assert timestamp not in self.inputs, f"Input for timestamp={timestamp} already exists in obj_id={self.obj_id}"
        self.inputs[timestamp] = new_input

    def add_aura(self, aura: Aura) -> None:
        assert aura.aura_id not in self.auras, f"Aura with ID ({aura.aura_id}) already exists."
        self.auras[aura.aura_id] = aura

    def get_aura(self, aura_id: Tuple[int, int, int]) -> Aura:
        assert aura_id in self.auras, f"Aura with ID ({aura_id}) does not exist."
        return self.auras.get(aura_id, Aura())

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


class Ruleset:
    """ Static game configuration that should not be changed after combat has started. """
    def __init__(self) -> None:
        self.obj_templates: Dict[int, GameObj] = {}
        self.spells: Dict[int, Spell] = {}
        self.populate_ruleset()

    def get_obj_template(self, template_id: int) -> GameObj:
        assert template_id in self.obj_templates, f"Obj template with ID {template_id} not found."
        return self.obj_templates.get(template_id, GameObj())

    def add_obj_template(self, template: GameObj) -> None:
        assert template.template_id not in self.obj_templates, f"Obj template with ID {template.template_id} already exists."
        self.obj_templates[template.template_id] = template

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells, f"Spell with ID {spell_id} not found."
        return self.spells.get(spell_id, Spell())

    def add_spell(self, spell: Spell) -> None:
        assert spell.spell_id not in self.spells, f"Spell with ID {spell.spell_id} already exists."
        self.spells[spell.spell_id] = spell

    def populate_ruleset(self) -> None:
        database = Database()
        for template in database.obj_templates:
            self.add_obj_template(template)
        for spell in database.spells:
            self.add_spell(spell)


class EventLog:
    """ A collection of logs for all combat events that have occurred. """
    def __init__(self) -> None:
        self._combat_event_log: Dict[int, CombatEvent] = {}

    def add_event(self, combat_event: CombatEvent):
        self._combat_event_log[combat_event.event_id] = combat_event
        print(combat_event.event_summary)


class World:
    """ The entire world state """
    def __init__(self) -> None:
        self.previous_timestamp: float = 0.0
        self.current_timestamp: float = 0.0

        self.event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self.game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self.environment: GameObj = GameObj(obj_id=self.game_obj_id_gen.new_id())
        self.player: Optional[GameObj] = None
        self.boss1: Optional[GameObj] = None
        self.boss2: Optional[GameObj] = None

        self.ruleset: Ruleset = Ruleset()
        self.auras: Dict[Tuple[int, int, int], Aura] = {}
        self.game_objs: Dict[int, GameObj] = {self.environment.obj_id: self.environment}
        self.combat_event_log: EventLog = EventLog()

    @property
    def delta_time(self) -> float:
        return self.current_timestamp - self.previous_timestamp


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

    def _handle_event(self, event: CombatEvent) -> EventOutcome:
        source_obj = self.get_game_obj(event.source)
        spell = self.ruleset.get_spell(event.spell)
        target_obj = TargetHandler.select_target(event, source_obj, spell, self)
        if not event.has_target:
            event = event.new_target(target_obj.obj_id)
        outcome = SpellValidator.decide_outcome(source_obj, spell, target_obj)
        if outcome == EventOutcome.SUCCESS:
            SpellHandler.handle_spell(source_obj, spell, target_obj, self)
            self.combat_event_log.add_event(event.finalize_outcome(outcome))
            if spell.is_spell_sequence:
                sequenced_event = event.continue_spell_sequence(self.event_id_gen.new_id(), spell.next_spell)
                self._handle_event(sequenced_event)

    def add_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self.game_objs, f"GameObj with ID {game_obj.obj_id} already exists."
        self.game_objs[game_obj.obj_id] = game_obj

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self.game_objs, f"GameObj with ID {obj_id} does not exist."
        return self.game_objs.get(obj_id, GameObj())


class SpellHandler:
    @staticmethod
    def handle_spell(source_obj: GameObj, spell: Spell, target_obj: GameObj, world: World) -> None:
        if spell.flags & (SpellFlag.SPAWN_NPC | SpellFlag.SPAWN_PLAYER | SpellFlag.SPAWN_BOSS):
            SpellHandler._handle_spawn(source_obj, spell, world)
        if spell.flags & SpellFlag.AURA:
            SpellHandler._handle_aura(source_obj, spell, target_obj, world)
        if spell.flags & (SpellFlag.MOVE_UP | SpellFlag.MOVE_LEFT | SpellFlag.MOVE_DOWN | SpellFlag.MOVE_RIGHT):
            SpellHandler._handle_movement(spell, target_obj, world)
        if spell.flags & SpellFlag.TAB_TARGET:
            SpellHandler._handle_tab_targeting(source_obj, world)
        if spell.flags & SpellFlag.DAMAGE:
            spell_power = spell.power * source_obj.spell_modifier
            target_obj.suffer_damage(spell_power)
        if spell.flags & SpellFlag.HEAL:
            spell_power = spell.power * source_obj.spell_modifier
            target_obj.restore_health(spell_power)

    @staticmethod
    def _handle_spawn(source_obj: GameObj, spell: Spell, world: World) -> None:
        obj_id = world.game_obj_id_gen.new_id()
        obj_template = world.ruleset.get_obj_template(spell.template_id)
        new_obj = GameObj.create_from_template(obj_id, source_obj.obj_id, obj_template)
        world.add_game_obj(new_obj)
        if spell.flags & SpellFlag.SPAWN_BOSS:
            if world.boss1 is None:
                world.boss1 = new_obj
            else:
                assert world.boss2 is None, "Second boss already exists."
                world.boss2 = new_obj
        if spell.flags & SpellFlag.SPAWN_PLAYER:
            assert world.player is None, "Player already exists."
            world.player = new_obj

    @staticmethod
    def _handle_aura(source_obj: GameObj, spell: Spell, target_obj: GameObj, world: World) -> None:
        aura_spell = world.ruleset.get_spell(spell.next_spell)
        aura = Aura.create_aura(world.current_timestamp, source_obj.obj_id, aura_spell, target_obj.obj_id)
        target_obj.add_aura(aura)

    @staticmethod
    def _handle_movement(spell: Spell, target_obj: GameObj, world: World) -> None:
        if spell.flags & SpellFlag.MOVE_UP:
            target_obj.move_in_direction(0.0, 1.0, target_obj.movement_speed, world.delta_time)
        if spell.flags & SpellFlag.MOVE_LEFT:
            target_obj.move_in_direction(-1.0, 0.0, target_obj.movement_speed, world.delta_time)
        if spell.flags & SpellFlag.MOVE_DOWN:
            target_obj.move_in_direction(0.0, -1.0, target_obj.movement_speed, world.delta_time)
        if spell.flags & SpellFlag.MOVE_RIGHT:
            target_obj.move_in_direction(1.0, 0.0, target_obj.movement_speed, world.delta_time)

    @staticmethod
    def _handle_tab_targeting(source_obj: GameObj, world: World) -> None:
        if not source_obj.is_allied:
            source_obj.current_target = world.player.obj_id
        elif source_obj.current_target == world.boss1.obj_id:
            source_obj.switch_target(world.boss2.obj_id)
        else:
            source_obj.switch_target(world.boss1.obj_id)


class TargetHandler:
    @staticmethod
    def select_target(event: CombatEvent, source: GameObj, spell: Spell, world: World) -> GameObj:
        if spell.flags & SpellFlag.SELF_CAST:
            return source
        if not IdGen.is_empty_id(event.target):
            return world.get_game_obj(event.target)
        if spell.flags & SpellFlag.DAMAGE:
            if source.is_allied:
                return world.boss1
            return world.player
        if spell.flags & SpellFlag.HEAL:
            return source
        return source

class SpellValidator:
    @staticmethod
    def decide_outcome(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> EventOutcome:
        # not implemented
        assert source_obj.obj_id + spell.spell_id + target_obj.obj_id > 0, "just a placeholder"
        return EventOutcome.SUCCESS


class InputHandler:

    @staticmethod
    def convert_to_events(id_gen: IdGen, timestamp: float, obj: GameObj, game_input: PlayerInput) -> List[CombatEvent]:
        spell_ids: List[int] = []
        spell_ids += [obj.move_up_id] if game_input.move_up else []
        spell_ids += [obj.move_left_id] if game_input.move_left else []
        spell_ids += [obj.move_down_id] if game_input.move_down else []
        spell_ids += [obj.move_right_id] if game_input.move_right else []
        spell_ids += [obj.next_target] if game_input.next_target else []
        spell_ids += [obj.ability_1_id] if game_input.ability_1 else []
        spell_ids += [obj.ability_2_id] if game_input.ability_2 else []
        spell_ids += [obj.ability_3_id] if game_input.ability_3 else []
        spell_ids += [obj.ability_4_id] if game_input.ability_4 else []
        assert IdGen.EMPTY_ID not in spell_ids, "Game input resulted in an empty spell being cast."
        events: List[CombatEvent] = []
        for spell_id in spell_ids:
            events.append(CombatEvent.create_from_input(id_gen.new_id(), timestamp, obj.obj_id, spell_id, obj.current_target))
        return events


class GameInstance:
    def __init__(self) -> None:
        self.world: World = World()

    def simulate_game_in_console(self) -> None:
        self.setup_game(300)
        SIMULATION_DURATION = 6
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of player input
            self.process_server_tick(1 / UPDATES_PER_SECOND, True, False, False, False, False, True, False, False, False)

    def setup_game(self, setup_spell_id: int) -> None:
        self.world.setup_game_obj(setup_spell_id)

    def process_server_tick(self, delta_time: float, move_up: bool, move_left: bool, move_down: bool, move_right: bool, next_target: bool, ability_1: bool, ability_2: bool, ability_3: bool, ability_4: bool) -> None:
        self.world.advance_combat(delta_time, PlayerInput(local_timestamp=self.world.current_timestamp, move_up=move_up, move_left=move_left, move_down=move_down, move_right=move_right, next_target=next_target, ability_1=ability_1, ability_2=ability_2, ability_3=ability_3, ability_4=ability_4))

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

    @staticmethod
    def create_player_input_dct(list_of_inputs: List[PlayerInput]) -> Dict[float, PlayerInput]:
        inputs_dct: SortedDict[float, PlayerInput] = SortedDict()
        for player_input in list_of_inputs:
            inputs_dct[player_input.local_timestamp] = player_input
        return inputs_dct

class Database:
    def __init__(self) -> None:
        self.spells: List[Spell] = Database.load_spell_collections()
        self.obj_templates: List[GameObj] = Database.load_obj_template_collections()

    @staticmethod
    def load_spell_collections() -> List[Spell]:
        spells: List[Spell] = []
        spells += Utils.load_collection(SpellCollectionCore)
        return spells

    @staticmethod
    def load_obj_template_collections() -> List[GameObj]:
        obj_templates: List[GameObj] = []
        obj_templates += Utils.load_collection(ObjTemplateCollectionCore)
        return obj_templates



class SpellCollectionCore:
    @staticmethod
    def empty_spell() -> Spell:
        return Spell(spell_id=0)

    @staticmethod
    def move_up() -> Spell:
        return Spell(spell_id=1, flags=SpellFlag.MOVE_UP | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def move_left() -> Spell:
        return Spell(spell_id=2, flags=SpellFlag.MOVE_LEFT | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def move_down() -> Spell:
        return Spell(spell_id=3, flags=SpellFlag.MOVE_DOWN | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def move_right() -> Spell:
        return Spell(spell_id=4, flags=SpellFlag.MOVE_RIGHT | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def tab_target() -> Spell:
        return Spell(spell_id=5, flags=SpellFlag.TAB_TARGET)

    @staticmethod
    def fireblast() -> Spell:
        return Spell(
            spell_id=100,
            power=3.0,
            flags=SpellFlag.DAMAGE,
        )

    @staticmethod
    def small_heal() -> Spell:
        return Spell(
            spell_id=101,
            duration=6.0,
            ticks=10,
            power=20.0,
            flags=SpellFlag.HEAL,
        )

    @staticmethod
    def healing_aura() -> Spell:
        return Spell(
            spell_id=102,
            next_spell=SpellCollectionCore.small_heal().spell_id,
            flags=SpellFlag.AURA | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def spawn_player() -> Spell:
        return Spell(
            spell_id=200,
            flags=SpellFlag.SPAWN_PLAYER | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def spawn_enemy() -> Spell:
        return Spell(
            spell_id=201,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def spawn_target_dummy() -> Spell:
        return Spell(
            spell_id=202,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def setup_test_zone() -> Spell:
        return Spell(
            spell_id=300,
            next_spell=SpellCollectionCore.setup_test_zone_seq1().spell_id,
        )

    @staticmethod
    def setup_test_zone_seq1() -> Spell:
        return SpellCollectionCore.spawn_enemy()._replace(
            spell_id=301,
            alias_id=SpellCollectionCore.spawn_enemy().spell_id,
            next_spell=SpellCollectionCore.setup_test_zone_seq2().spell_id,
        )

    @staticmethod
    def setup_test_zone_seq2() -> Spell:
        return SpellCollectionCore.spawn_target_dummy()._replace(
            spell_id=302,
            alias_id=SpellCollectionCore.spawn_target_dummy().spell_id,
            next_spell=SpellCollectionCore.spawn_player().spell_id,
        )


class ObjTemplateCollectionCore:
    @staticmethod
    def empty_obj() -> GameObj:
        return GameObj(
            template_id=0,
        )

    @staticmethod
    def player_template() -> GameObj:
        return GameObj(
            template_id=SpellCollectionCore.spawn_player().spell_id,
            hp=30.0,
            is_allied=True,
            x=0.3,
            y=0.3,
            move_up_id=SpellCollectionCore.move_up().spell_id,
            move_left_id=SpellCollectionCore.move_left().spell_id,
            move_down_id=SpellCollectionCore.move_down().spell_id,
            move_right_id=SpellCollectionCore.move_right().spell_id,
            next_target=SpellCollectionCore.tab_target().spell_id,
            ability_1_id=SpellCollectionCore.fireblast().spell_id,
            ability_2_id=SpellCollectionCore.fireblast().spell_id,
            ability_3_id=SpellCollectionCore.fireblast().spell_id,
            ability_4_id=SpellCollectionCore.fireblast().spell_id,
        )

    @staticmethod
    def enemy_template() -> GameObj:
        return GameObj(
            template_id=SpellCollectionCore.spawn_enemy().spell_id,
            hp=30.0,
            x=0.7,
            y=0.7,
            ability_1_id=SpellCollectionCore.small_heal().spell_id,
            ability_2_id=SpellCollectionCore.healing_aura().spell_id,
            inputs=Utils.create_player_input_dct([
                PlayerInput(local_timestamp=3.0, ability_1=True),
                PlayerInput(local_timestamp=5.0, ability_2=True),
            ]),
        )

    @staticmethod
    def target_dummy_template() -> GameObj:
        return GameObj(
            template_id=SpellCollectionCore.spawn_target_dummy().spell_id,
            hp=80.0,
            x=0.5,
            y=0.8,
            ability_1_id=SpellCollectionCore.fireblast().spell_id,
            inputs=Utils.create_player_input_dct([
                PlayerInput(local_timestamp=4.0, ability_1=True),
            ]),
        )

#%%
if __name__ == "__main__":
    manager = GameInstance()
    manager.simulate_game_in_console()