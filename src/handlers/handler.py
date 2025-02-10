from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
from typing import Any, Dict, List, Tuple, Type, ValuesView, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json
from src.config.color import Color
from src.model.models import IdGen, SpellFlag, Spell, Aura, PlayerInput, EventTrigger, EventOutcome, CombatEvent, GameObjStatus, GameObj
from src.utils.utils import Utils
from src.config.spell_db import Database

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
        self.player: GameObj = self.environment
        self.boss1: GameObj = self.environment
        self.boss2: GameObj = self.environment

        self.ruleset: Ruleset = Ruleset()
        self.auras: Dict[Tuple[int, int, int], Aura] = {}
        self.game_objs: Dict[int, GameObj] = {self.environment.obj_id: self.environment}
        self.combat_event_log: EventLog = EventLog()

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
        if spell.flags & SpellFlag.TRIGGER_GCD:
            print(source_obj.gcd_progress)
            source_obj.gcd_start = world.current_timestamp
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
        aura_spell = world.ruleset.get_spell(spell.next_spell)
        aura = Aura.create_from_spell(world.current_timestamp, source_obj.obj_id, aura_spell, target_obj.obj_id)
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
            # example of player input
            self.process_server_tick(1 / UPDATES_PER_SECOND, True, False, False, False, False, True, False, False, False)

    def setup_game(self, setup_spell_id: int) -> None:
        self.world.setup_game_obj(setup_spell_id)

    def process_server_tick(self, delta_time: float, move_up: bool, move_left: bool, move_down: bool, move_right: bool, next_target: bool, ability_1: bool, ability_2: bool, ability_3: bool, ability_4: bool) -> None:
        self.world.advance_combat(delta_time, PlayerInput(local_timestamp=self.world.current_timestamp, move_up=move_up, move_left=move_left, move_down=move_down, move_right=move_right, next_target=next_target, ability_1=ability_1, ability_2=ability_2, ability_3=ability_3, ability_4=ability_4))

    def get_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self.world.game_objs.values()


#%%
if __name__ == "__main__":
    manager = GameInstance()
    manager.simulate_game_in_console()