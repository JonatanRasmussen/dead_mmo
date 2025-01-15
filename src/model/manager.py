from typing import Dict, Set, List, Tuple, Final, Optional
from enum import Enum

class Spell:
    def __init__(self, spell_id: int) -> None:
        self.spell_id: Final[int] = spell_id

        self.setup_spell_id: int = 0
        self.finish_spell_id: int = 0

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

        self.flag_is_channel: bool = False
        self.flag_spawn_npc: bool = False
        self.flag_update_pos: bool = False
        self.flag_try_move: bool = False
        self.flag_force_move: bool = False

        self.flag_player_movement: bool = False

    @classmethod
    def create_empty(cls) -> 'Spell':
        return Spell(IdGenerator.EMPTY_ID)


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
        self.target_obj_id: int = 0
        self.local_time: float = 0.0
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
        self.ignore_pos: bool = False

    @classmethod
    def create_empty(cls) -> 'Pos':
        return Pos()


class Npc:
    def __init__(self, npc_id: int) -> None:
        self.npc_id: Final[int] = npc_id
        self.spell_id: int = 0

    @classmethod
    def create_empty(cls) -> 'Npc':
        return Npc(IdGenerator.EMPTY_ID)

    def is_empty(self) -> bool:
        return self.npc_id == IdGenerator.EMPTY_ID


class GameObj:
    def __init__(self, obj_id: int) -> None:
        self.obj_id: Final[int] = obj_id
        self.npc: Npc = Npc.create_empty()
        self.position: Pos = Pos()
        self.hp: float = 0.0

    @classmethod
    def create_empty(cls) -> 'GameObj':
        return GameObj(IdGenerator.EMPTY_ID)

    def is_empty(self) -> bool:
        return self.obj_id == IdGenerator.EMPTY_ID

    def get_spell_modifier(self) -> float:
        #calculation not yet implemented
        return 1.0

    def suffer_damage(self, spell_power: float) -> None:
        self.hp -= spell_power


class EventOutcome(Enum):
    EMPTY = 0
    PENDING = 1
    SUCCESS = 2
    FAILED = 3
    MISSED = 4

class CombatEvent:
    def __init__(self, event_id: int, timestamp: float, source: GameObj, act: Spell, dest: Pos) -> None:
        self.event_id: Final[int] = event_id
        self.timestamp: float = timestamp
        self.source: GameObj = source
        self.spell: Spell = act
        self.dest: Pos = dest
        self.targeted_obj: GameObj = GameObj.create_empty()
        self.outcome: EventOutcome = EventOutcome.EMPTY


    @classmethod
    def create_empty(cls) -> 'CombatEvent':
        return CombatEvent(IdGenerator.EMPTY_ID, 0.0, GameObj.create_empty(), Spell.create_empty(), Pos.create_empty())

    def is_empty(self) -> bool:
        return self.event_id == IdGenerator.EMPTY_ID

    def decide_outcome(self) -> None:
        #not implemented
        self.outcome = EventOutcome.SUCCESS


class Zone:
    def __init__(self, zone_id: int) -> None:
        self.zone_id: Final[int] = zone_id

    @classmethod
    def create_empty(cls) -> 'Zone':
        return Zone(IdGenerator.EMPTY_ID)

    def is_empty(self) -> bool:
        return self.zone_id == IdGenerator.EMPTY_ID



class World:
    def __init__(self, world_id: int) -> None:
        self.world_id: Final[int] = world_id
        self.timestamp: float = 0.0
        self.auras: Dict[int, Aura] = {}
        self.game_objs: Dict[int, GameObj] = {}
        self.combat_event_log: List[str] = []

    @classmethod
    def create_empty(cls) -> 'World':
        return World(IdGenerator.EMPTY_ID)

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self.game_objs
        return self.game_objs.get(obj_id, GameObj.create_empty())

    def get_aura(self, aura_id: int) -> Aura:
        assert aura_id in self.auras
        return self.auras.get(aura_id, Aura.create_empty())


class IdGenerator:
    EMPTY_ID = 0

    def __init__(self) -> None:
        self._next_id: int = 0
        self._reserved_ids: Set[int] = set()

    def new_id(self) -> int:
        self._next_id += 1
        while self._next_id in self._reserved_ids:
            self._next_id += 1
        return self._next_id

    def reserve_id(self, reserved_id: int) -> None:
        self._reserved_ids.add(reserved_id)


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
        templates = Database()
        for npc in templates.npcs:
            self.add_npc(npc)
        for spell in templates.spells:
            self.add_spell(spell)
        for zone in templates.zones:
            self.add_zone(zone)


class PlayerInput:
    def __init__(self) -> None:
        self.event_id_gen: IdGenerator = IdGenerator()
        self.combat_events: List[CombatEvent] = []
        self.is_pressing_move_up: bool = False
        self.is_pressing_move_down: bool = False
        self.is_pressing_move_left: bool = False
        self.is_pressing_move_right: bool = False
        self.is_pressing_ability_1: bool = False
        self.is_pressing_ability_2: bool = False
        self.is_pressing_ability_3: bool = False
        self.is_pressing_ability_4: bool = False

    def reset_to_empty_input(self) -> None:
        self.is_pressing_move_up = False
        self.is_pressing_move_down = False
        self.is_pressing_move_left = False
        self.is_pressing_move_right = False
        self.is_pressing_ability_1 = False
        self.is_pressing_ability_2 = False
        self.is_pressing_ability_3 = False
        self.is_pressing_ability_4 = False

    def create_combat_events(self) -> None:
        if self.is_moving():
            pos: Pos = Pos()
            if self.is_pressing_move_up:
                pos.pos_y += 1.0
            if self.is_pressing_move_left:
                pos.pos_x -= 1.0
            if self.is_pressing_move_down:
                pos.pos_y -= 1.0
            if self.is_pressing_move_right:
                pos.pos_x += 1.0
            event_id = self.event_id_gen.new_id()
            #to be done: implement serialized combat event


    def is_moving(self) -> bool:
        return (self.is_pressing_move_up or
                self.is_pressing_move_down or
                self.is_pressing_move_left or
                self.is_pressing_move_right)

class Manager:
    def __init__(self) -> None:
        self.aura_id_gen: IdGenerator = IdGenerator()
        self.event_id_gen: IdGenerator = IdGenerator()
        self.game_obj_id_gen: IdGenerator = IdGenerator()
        self.ruleset: Ruleset = Ruleset()
        self.world: World = World.create_empty()
        self.player_input: PlayerInput = PlayerInput()
        self.current_events: List[CombatEvent] = []

    def execute_combat_for_next_timestamp(self, delta_time: float) -> None:
        self.update_auras(delta_time)
        self.process_combat_events()

    def update_auras(self, delta_time: float) -> None:
        aura_ids: List[int] = sorted(self.world.auras.keys())
        for aura_id in aura_ids:
            aura = self.world.get_aura(aura_id)
            aura.update_timers(delta_time)
            if aura.try_process_tick():
                self.create_combat_event_for_aura_tick(aura)

    def create_combat_event_for_aura_tick(self, aura: Aura) -> None:
        event_id = self.event_id_gen.new_id()
        timestamp = self.world.timestamp
        source = self.world.get_game_obj(aura.source_id)
        act = self.ruleset.get_spell(aura.spell_id)
        dest = self.world.get_game_obj(aura.target_id).position
        event = CombatEvent(event_id, timestamp, source, act, dest)
        event.targeted_obj = self.world.get_game_obj(dest.target_obj_id)
        event.outcome = EventOutcome.PENDING
        self.current_events.append(event)

    def process_combat_events(self) -> None:
        for event in self.current_events:
            event.decide_outcome()
            if event.outcome == EventOutcome.SUCCESS:
                spell_power = event.spell.power * event.source.get_spell_modifier()
                event.targeted_obj.suffer_damage(spell_power)
        self.current_events.clear()


class Database:
    def __init__(self) -> None:
        self.npcs: List[Npc] = [

        ]
        self.spells: List[Spell] = [
            Database.empty_spell(),
            Database.player_movement(),
        ]
        self.zones: List[Zone] = [

        ]

    @staticmethod
    def empty_spell() -> Spell:
        return Spell(0)

    @staticmethod
    def player_movement() -> Spell:
        spell = Spell(1)
        spell.flag_player_movement = True
        return spell

    @staticmethod
    def test_st_insta() -> Spell:
        spell = Spell(2)
        spell.range_limit = 99999.0
        spell.power = 10.0
        return spell
