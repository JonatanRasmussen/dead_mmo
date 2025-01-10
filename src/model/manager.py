from typing import Dict, List, Tuple, Final, Optional

class IdGen:
    EMPTY_ID = 0

    def __init__(self) -> None:
        self._aura_next_id: int = 0
        self._combat_event_next_id: int = 0
        self._game_obj_next_id: int = 0

    def new_aura_id(self) -> int:
        self._aura_next_id += 1
        return self._aura_next_id

    def new_combat_event_id(self) -> int:
        self._combat_event_next_id += 1
        return self._combat_event_next_id

    def new_game_obj_id(self) -> int:
        self._game_obj_next_id += 1
        return self._game_obj_next_id


class Spell:
    def __init__(self, spell_id: int) -> None:
        self.spell_id: Final[int] = spell_id

        self.setup_spell_id: int = 0
        self.finish_spell_id: int = 0

        self.power: float = 0

        self.range_limit: float = 0
        self.cost: float = 0
        self.cast_time: float = 0
        self.duration: float = 0
        self.ticks: int = 0
        self.cooldown: float = 0
        self.max_stacks: int = 0
        self.gcd_mod: float = 0
        self.knockback: float = 0

        self.flag_is_channel: bool = False
        self.flag_spawn_npc: bool = False
        self.flag_update_pos: bool = False
        self.flag_try_move: bool = False
        self.flag_force_move: bool = False

    @classmethod
    def create_empty(cls) -> 'Spell':
        return Spell(IdGen.EMPTY_ID)


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
        return Aura(IdGen.EMPTY_ID, IdGen.EMPTY_ID, IdGen.EMPTY_ID, Spell.create_empty())

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

    def process_tick_if_ready(self) -> bool:
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
        return Npc(IdGen.EMPTY_ID)


class GameObj:
    def __init__(self, obj_id: int) -> None:
        self.obj_id: Final[int] = obj_id
        self.npc: Npc = Npc.create_empty()
        self.position: Pos = Pos()

    @classmethod
    def create_empty(cls) -> 'GameObj':
        return GameObj(IdGen.EMPTY_ID)


class CombatEvent:
    def __init__(self, event_id: int, timestamp: float, source: GameObj, act: Spell, dest: Pos) -> None:
        self.event_id: Final[int] = event_id
        self.timestamp: float = timestamp
        self.source: GameObj = source
        self.spell: Spell = act
        self.dest: Pos = dest

    @classmethod
    def create_empty(cls) -> 'CombatEvent':
        return CombatEvent(IdGen.EMPTY_ID, 0.0, GameObj.create_empty(), Spell.create_empty(), Pos.create_empty())


class Zone:
    def __init__(self, zone_id: int) -> None:
        self.zone_id: Final[int] = zone_id

    @classmethod
    def create_empty(cls) -> 'Zone':
        return Zone(IdGen.EMPTY_ID)


class World:
    def __init__(self, world_id: int) -> None:
        self.world_id: Final[int] = world_id
        self.timestamp: float = 0.0
        self.auras: Dict[int, Aura] = {}
        self.game_objs: Dict[int, GameObj] = {}
        self.combat_event_log: List[str] = []

    @classmethod
    def create_empty(cls) -> 'World':
        return World(IdGen.EMPTY_ID)

    def get_game_obj(self, obj_id: int) -> GameObj:
        return self.game_objs.get(obj_id, GameObj.create_empty())

    def get_aura(self, aura_id: int) -> Aura:
        return self.auras.get(aura_id, Aura.create_empty())


class Ruleset:
    def __init__(self) -> None:
        self.npcs: Dict[int, Npc] = {}
        self.spells: Dict[int, Spell] = {}
        self.zones: Dict[int, Zone] = {}

    def get_npc(self, npc_id: int) -> Npc:
        return self.npcs.get(npc_id, Npc.create_empty())

    def get_spell(self, spell_id: int) -> Spell:
        return self.spells.get(spell_id, Spell.create_empty())

    def get_zone(self, zone_id: int) -> Zone:
        return self.zones.get(zone_id, Zone.create_empty())


class Manager:
    def __init__(self) -> None:
        self.delta_time: float = 0.0
        self.world: World = World.create_empty()
        self.combat_events: List[CombatEvent] = []
        self.id_generator: IdGen = IdGen()
        self.ruleset: Ruleset = Ruleset()

    def execute_combat_for_next_timestamp(self, delta_time: float) -> None:
        self.update_timers_and_fetch_events(delta_time)
        self.handle_combat_events()

    def update_timers_and_fetch_events(self, delta_time: float) -> None:
        aura_ids: List[int] = sorted(self.world.auras.keys())
        for aura_id in aura_ids:
            aura = self.world.get_aura(aura_id)
            aura.update_timers(delta_time)
            if aura.process_tick_if_ready():
                event_id = self.id_generator.new_combat_event_id()
                timestamp = self.world.timestamp
                source = self.world.get_game_obj(aura.source_id)
                act = self.ruleset.get_spell(aura.spell_id)
                dest = self.world.get_game_obj(aura.target_id).position
                self.combat_events.append(CombatEvent(event_id, timestamp, source, act, dest))

    def handle_combat_events(self) -> None:
        # this is todo (finish tomorrow)
        pass
