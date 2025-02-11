from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
from typing import Any, Dict, List, Tuple, Type, ValuesView, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
import heapq
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json
from src.config.color import Color
from src.model.models import IdGen, SpellFlag, Spell, Aura, Controls, EventTrigger, EventOutcome, CombatEvent, GameObjStatus, GameObj
from src.utils.utils import Utils
from src.config.spell_db import Database

class Ruleset:
    """ Static game configuration that should not be changed after combat has started. """
    def __init__(self) -> None:
        self.spells: Dict[int, Spell] = {}
        self.populate_ruleset()

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells, f"Spell with ID {spell_id} not found."
        return self.spells.get(spell_id, Spell())

    def add_spell(self, spell: Spell) -> None:
        assert spell.spell_id not in self.spells, f"Spell with ID {spell.spell_id} already exists."
        self.spells[spell.spell_id] = spell

    def populate_ruleset(self) -> None:
        database = Database()
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
        self.player: GameObj = self.environment
        self.boss1: GameObj = self.environment
        self.boss2: GameObj = self.environment

        self.ruleset: Ruleset = Ruleset()

        self.auras: SortedDict[Tuple[int, int, int], Aura] = SortedDict()
        self.controls: SortedDict[Tuple[float, int], Controls] = SortedDict()

        self.game_objs: Dict[int, GameObj] = {self.environment.obj_id: self.environment}
        self.combat_event_log: EventLog = EventLog()

        self.events: List[Tuple[float, int, int, CombatEvent]] = []


    @property
    def delta_time(self) -> float:
        return self.current_timestamp - self.previous_timestamp

    @property
    def player_exists(self) -> float:
        return self.player.obj_id != self.environment.obj_id
    @property
    def boss1_exists(self) -> float:
        return self.boss1.obj_id != self.environment.obj_id
    @property
    def boss2_exists(self) -> float:
        return self.boss2.obj_id != self.environment.obj_id

    def setup_game_obj(self, setup_spell_id: int) -> None:
        setup_event = CombatEvent(
            event_id=self.event_id_gen.new_id(),
            timestamp=self.current_timestamp,
            source=self.environment.obj_id,
            spell=setup_spell_id,
        )
        self._handle_event(setup_event)

    def advance_combat(self, delta_time: float, controls: Controls) -> None:
        self.previous_timestamp = self.current_timestamp
        self.current_timestamp += delta_time
        if self.player_exists:
            self.add_controls(self.player.obj_id, self.current_timestamp, controls)
        assert len(self.events) == 0, "Events not empty. This should not happen."
        self.fetch_events_in_time_range()
        max_iterations = 10_000
        while self.events:
            assert max_iterations > 0, "Infinite loop detected."
            max_iterations -= 1
            _, _, _, event = heapq.heappop(self.events)
            self._handle_event(event)


    def fetch_events_in_time_range(self) -> None:
        events: List[CombatEvent] = []
        # Handle aura ticks
        for aura in self.auras.values():
            if aura.has_tick_this_frame(self.previous_timestamp, self.current_timestamp):
                events.append(CombatEvent.create_from_aura_tick(self.event_id_gen.new_id(), self.current_timestamp, aura))
        # Handle controls
        start_key: Tuple[float, int] = (self.previous_timestamp, min(self.game_objs.keys()))
        end_key: Tuple[float, int] = (self.current_timestamp, max(self.game_objs.keys()))
        for timestamp, obj_id in self.controls.irange(start_key, end_key):
            if timestamp == self.previous_timestamp:
                continue # Prevent double processing of controls
            controls: Controls = self.controls[(timestamp, obj_id)]
            game_obj = self.get_game_obj(obj_id)
            events += game_obj.convert_to_events(self.event_id_gen, controls.local_timestamp, controls)
        for event in events:
            heapq.heappush(self.events, (event.timestamp, event.source, event.event_id, event))


    def _handle_event(self, event: CombatEvent) -> None:
        source_obj = self.get_game_obj(event.source)
        spell = self.ruleset.get_spell(event.spell)
        target_obj = TargetHandler.select_target(event, source_obj, spell, self)
        if not event.has_target:
            event = event.new_target(target_obj.obj_id)
        outcome = SpellValidator.decide_outcome(source_obj, spell, target_obj)
        if outcome == EventOutcome.SUCCESS:
            SpellHandler.handle_spell(source_obj, spell, target_obj, self)
            if spell.spell_sequence is not None:
                for next_spell in spell.spell_sequence:
                    sequenced_event = event.continue_spell_sequence(self.event_id_gen.new_id(), next_spell)
                    self._handle_event(sequenced_event)
        self.combat_event_log.add_event(event.finalize_outcome(outcome))

    def add_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self.game_objs, f"GameObj with ID {game_obj.obj_id} already exists."
        self.game_objs[game_obj.obj_id] = game_obj

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self.game_objs, f"GameObj with ID {obj_id} does not exist."
        return self.game_objs.get(obj_id, GameObj())

    def add_controls(self, obj_id: int, timestamp: float, new_controls: Controls) -> None:
        key: Tuple[float, int] = (timestamp, obj_id)
        assert key not in self.controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self.controls[key] = new_controls

    def add_aura(self, aura: Aura) -> None:
        key: Tuple[int, int, int] = aura.aura_id
        assert key not in self.auras, f"Aura with (source, spell, target) = ({key}) already exists."
        self.auras[key] = aura

    def get_aura(self, aura_id: Tuple[int, int, int]) -> Aura:
        key = aura_id
        assert key in self.auras, f"Aura with ID ({aura_id}) does not exist."
        return self.auras.get(key, Aura())

    def get_obj_auras(self, obj_id: int) -> List[Aura]:
        return [aura for aura in self.auras.values() if aura.target_id == obj_id]

class SpellHandler:
    @staticmethod
    def handle_spell(source_obj: GameObj, spell: Spell, target_obj: GameObj, world: World) -> None:
        if spell.spawned_obj is not None:
            SpellHandler._handle_spawn(source_obj, spell, world)
        if spell.flags & SpellFlag.AURA:
            SpellHandler._handle_aura(source_obj, spell, target_obj, world)
        if spell.flags & (SpellFlag.MOVE_UP | SpellFlag.MOVE_LEFT | SpellFlag.MOVE_DOWN | SpellFlag.MOVE_RIGHT):
            SpellHandler._handle_movement(spell, target_obj, world)
        if spell.flags & SpellFlag.TAB_TARGET:
            SpellHandler._handle_tab_targeting(source_obj, world)
        if spell.flags & SpellFlag.TRIGGER_GCD:
            source_obj.gcd_start = world.current_timestamp
        if spell.flags & SpellFlag.DAMAGE:
            spell_power = spell.power * source_obj.spell_modifier
            target_obj.suffer_damage(spell_power)
        if spell.flags & SpellFlag.HEAL:
            spell_power = spell.power * source_obj.spell_modifier
            target_obj.restore_health(spell_power)

    @staticmethod
    def _handle_spawn(source_obj: GameObj, spell: Spell, world: World) -> None:
        if spell.spawned_obj is not None:
            obj_id = world.game_obj_id_gen.new_id()
            new_obj = GameObj.create_from_template(obj_id, source_obj.obj_id, spell.spawned_obj)
            world.add_game_obj(new_obj)
            if spell.controls is not None:
                for controls in spell.controls:
                    world.add_controls(obj_id, controls.local_timestamp, controls)
        if spell.flags & SpellFlag.SPAWN_BOSS:
            if not world.boss1_exists:
                world.boss1 = new_obj
            else:
                assert not world.boss2_exists, "Second boss already exists."
                world.boss2 = new_obj
        if spell.flags & SpellFlag.SPAWN_PLAYER:
            assert not world.player_exists, "Player already exists."
            world.player = new_obj

    @staticmethod
    def _handle_aura(source_obj: GameObj, spell: Spell, target_obj: GameObj, world: World) -> None:
        aura = Aura.create_from_spell(world.current_timestamp, source_obj.obj_id, spell, target_obj.obj_id)
        world.add_aura(aura)

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
        elif source_obj.current_target == world.boss1.obj_id and world.boss2_exists:
            source_obj.switch_target(world.boss2.obj_id)
        elif world.boss1_exists:
            source_obj.switch_target(world.boss1.obj_id)
        else:
            source_obj.switch_target(world.player.obj_id)
            # Not implemented. For now, let's assume boss1 always exist.


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


class GameInstance:
    def __init__(self) -> None:
        self.world: World = World()

    def simulate_game_in_console(self) -> None:
        self.setup_game(300)
        SIMULATION_DURATION = 6
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of controls
            self.process_server_tick(1 / UPDATES_PER_SECOND, True, False, False, False, False, True, False, False, False)

    def setup_game(self, setup_spell_id: int) -> None:
        self.world.setup_game_obj(setup_spell_id)

    def process_server_tick(self, delta_time: float, move_up: bool, move_left: bool, move_down: bool, move_right: bool, next_target: bool, ability_1: bool, ability_2: bool, ability_3: bool, ability_4: bool) -> None:
        self.world.advance_combat(delta_time, Controls(local_timestamp=self.world.current_timestamp, move_up=move_up, move_left=move_left, move_down=move_down, move_right=move_right, next_target=next_target, ability_1=ability_1, ability_2=ability_2, ability_3=ability_3, ability_4=ability_4))

    def get_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self.world.game_objs.values()


#%%
if __name__ == "__main__":
    manager = GameInstance()
    manager.simulate_game_in_console()