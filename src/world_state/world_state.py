from typing import Any, Iterable, Optional
from dataclasses import dataclass

from src.settings import Consts
from src.world_state import Controls, KeyPresses
from ._aura_handler import Aura, AuraHandler
from ._event_log import EventLog
from ._frame_heap import FrameHeap
from ._id_gen import IdGen
from ._spell_database import SpellDatabase
from ._event_system import EventSystem, UpcomingEvent, Outcome
from ._controls_system import ControlsSystem
from ._combat_system import CombatSystem
from ._movement_system import MovementSystem
from ._targeting_system import TargetingSystem
from ._vfx_and_sfx_system import VfxAndSfxSystem


@dataclass(slots=True)
class DisplayObj:
    obj_id: int
    pos_xy: tuple[float, float]
    size: float
    color_rgb: tuple[int, int, int]
    sprite_name: str


class WorldState:
    """ The entirely ECS-driven game state of the save file that is currently in use """

    def __init__(self) -> None:
        self.spell_database: SpellDatabase = SpellDatabase()
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}

        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self._active_obj_ids: set[int] = set()
        self._auras: AuraHandler = AuraHandler(self.spell_database)
        self._event_system = EventSystem(self.spell_database)
        self._controls_system = ControlsSystem(self.spell_database)
        self._movement_system = MovementSystem(self.spell_database)
        self._combat_system = CombatSystem(self.spell_database)
        self._targeting_system = TargetingSystem(self.spell_database)
        self._vfx_and_sfx_system = VfxAndSfxSystem(self.spell_database)

        self._create_environment_obj()

    @property
    def view_obj_ids(self) -> set[int]:
        return self._active_obj_ids

    @property
    def view_event_logs(self) -> dict[int, EventLog]:
        return self._event_log_for_each_frame

    def get_display_obj(self, obj_id: int, timestamp: int) -> DisplayObj | None:
        if not self._combat_system.is_visible(obj_id):
            return None
        obj_vfx = self._vfx_and_sfx_system.get_obj_visuals(obj_id)
        if not obj_vfx:
            return None
        try:
            x, y = self._movement_system.get_position(obj_id, timestamp)
        except ValueError:
            # Object was likely despawned between ticks.
            return None
        return DisplayObj(
            obj_id=obj_id,
            pos_xy=(x, y),
            size=self._combat_system.get_size(obj_id),
            color_rgb=obj_vfx.color,
            sprite_name=obj_vfx.sprite_name,
        )

    def get_spell_ids_for_successful_events(self, timestamp: int) -> Iterable[int]:
        return self._event_log_for_each_frame[timestamp].get_successful_spell_ids

    def process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> None:
        source_id = self._targeting_system.default_ids.environment_id
        for spell_id in setup_spell_ids:
            setup_event = UpcomingEvent(
                event_id=self._event_id_gen.generate_new_id(),
                timestamp=ingame_time,
                source_id=source_id,
                spell_id=spell_id
            )
            self._event_heap.insert_event(setup_event)

        empty_list_of_player_inputs: list[str] = []
        self.process_frame(empty_list_of_player_inputs, ingame_time)

    def process_frame(self, player_inputs: list[str], frame_end: int) -> None:
        """Execute state updates for current frame"""
        for controls_event in self._create_events_from_controls(player_inputs, frame_end):
            self._event_heap.insert_event(controls_event)

        event_log = EventLog()

        while self._event_heap.has_unprocessed_events(frame_end):
            u_event = self._event_heap.pop_next_event()
            assert u_event.timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {u_event}."

            f_event = self._finalize_and_process_event(u_event)
            event_log.log_event(f_event)

        self._event_log_for_each_frame[frame_end] = event_log

    def _finalize_and_process_event(self, u_event: UpcomingEvent) -> UpcomingEvent:
        target_id = self._targeting_system.decide_targeting(
            u_event.target_id, u_event.is_aoe_targeting, u_event.source_id, u_event.spell_id
        )

        expired_aura = u_event.is_aura_tick and not self._auras.aura_exists(u_event.aura_id)
        outcome = self._decide_outcome(
            u_event.timestamp, u_event.source_id, u_event.spell_id, target_id, expired_aura, u_event.is_aoe_targeting
        )

        f_event = u_event.finalize_event(u_event.source_id, target_id, outcome)
        self._process_event(f_event)
        return f_event

    def _process_event(self, f_event: UpcomingEvent) -> None:
        timestamp = f_event.timestamp
        source_id = f_event.source_id
        target_id = f_event.target_id
        spell_id = f_event.spell_id

        if f_event.outcome_is_valid:
            # We duck-type the spell database to fetch data flags dynamically
            # without ever needing to import the actual `Spell` object definition.
            spell = self.spell_database.get_spell(spell_id)

            new_obj_id = None
            if spell.spawned_obj is not None:
                new_obj_id = self.handle_spawn(timestamp, source_id, spell_id, target_id)

            if spell.has_aura_cancel:
                self._auras.remove_aura(source_id, spell.effect_id, target_id)

            new_aura_id = Consts.EMPTY_ID
            if spell.has_aura_apply:
                new_aura_id = self._auras.add_aura(timestamp, source_id, spell_id, target_id)

            if spell.has_cascading_events:
                for cascading_event in self._fetch_cascading_events(f_event, new_obj_id, source_id, spell_id, target_id, new_aura_id):
                    self._event_heap.insert_event(cascading_event)

            self._controls_system.apply_controls_event(timestamp, source_id, spell_id)
            self._combat_system.apply_combat_event(timestamp, source_id, spell_id, target_id)
            self._movement_system.apply_movement_event(timestamp, source_id, spell_id, target_id)
            self._targeting_system.apply_targeting_event(timestamp, source_id, spell_id, target_id)

    def _decide_outcome(self, timestamp: int, source_id: int, spell_id: int, target_id: int, expired_aura: bool, is_aoe_targeting: bool) -> Outcome:
        if expired_aura:
            return Outcome.AURA_NO_LONGER_EXISTS
        if not is_aoe_targeting:
            if not self._targeting_system.is_valid_source(source_id):
                return Outcome.SOURCE_IS_DISABLED
            if not self._controls_system.is_gcd_ready(source_id, spell_id, timestamp):
                return Outcome.GCD_NOT_READY
        if not self._targeting_system.is_valid_target(target_id) and not source_id == target_id:
            return Outcome.TARGET_IS_INVALID
        if not self._movement_system.is_within_range(timestamp, source_id, spell_id, target_id):
            return Outcome.OUT_OF_RANGE
        return Outcome.SUCCESS

    def handle_spawn(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        new_obj_id = self._game_obj_id_gen.generate_new_id()
        self._active_obj_ids.add(new_obj_id)
        self._movement_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id)
        self._combat_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
        self._controls_system.spawn_game_obj(new_obj_id, spell_id)
        self._targeting_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
        self._vfx_and_sfx_system.spawn_game_obj(new_obj_id, spell_id)
        return new_obj_id

    def _fetch_cascading_events(
        self,
        u_event: UpcomingEvent,
        new_obj_id: Optional[int],
        source_id: int,
        spell_id: int,
        target_id: int,
        new_aura_id: int
    ) -> Iterable[UpcomingEvent]:

        # 1. Spawned Object Control Events
        if new_obj_id is not None:
            new_obj_target_id = self._targeting_system.game_obj_targeting_dct[new_obj_id].current_target_id
            scripted_spells = self._controls_system.get_scripted_spells(new_obj_id, u_event.timestamp)

            for s_id, trigger_timestamp, priority in scripted_spells:
                yield UpcomingEvent(
                    event_id=self._event_id_gen.generate_new_id(),
                    timestamp=trigger_timestamp,
                    source_id=new_obj_id,
                    spell_id=s_id,
                    target_id=new_obj_target_id,
                    priority=priority,
                )

        # 2. Area of Effect (AoE) Events
        if self._targeting_system.is_area_of_effect(spell_id) and not u_event.is_aoe_targeting:
            target_ids = self._targeting_system.select_targets_for_aoe(source_id, target_id)
            priority = u_event.priority

            for aoe_target_id in target_ids:
                priority += 1
                aoe_copy = u_event.create_copy()
                aoe_copy.event_id = self._event_id_gen.generate_new_id()
                aoe_copy.priority = priority
                aoe_copy.target_id = aoe_target_id
                aoe_copy.is_aoe_targeting = True
                yield aoe_copy

        # 3. Spell Sequence Events
        sequenced_spells = self._targeting_system.get_spell_sequence(spell_id)
        if sequenced_spells is not None:
            priority = u_event.priority

            for next_spell_id in sequenced_spells:
                priority += 1
                seq_copy = u_event.create_copy()
                seq_copy.event_id = self._event_id_gen.generate_new_id()
                seq_copy.priority = priority
                seq_copy.spell_id = next_spell_id
                seq_copy.is_spell_sequence = True
                yield seq_copy

        # 4. Aura Tick Events
        if self._targeting_system.has_aura_apply(spell_id):
            aura = self._auras.get_aura_by_id(new_aura_id)
            priority = 0

            for tick_timestamp in aura.tick_timestamps:
                priority += 1
                yield UpcomingEvent(
                    event_id=self._event_id_gen.generate_new_id(),
                    timestamp=tick_timestamp,
                    source_id=aura.source_id,
                    spell_id=aura.periodic_spell_id,
                    target_id=aura.target_id,
                    priority=priority,
                    aura_id=aura.aura_id,
                    aura_origin_spell_id=aura.origin_spell_id,
                )

    def _create_events_from_controls(self, player_inputs: list[str], timestamp: int) -> Iterable[UpcomingEvent]:
        player_id = self._targeting_system.default_ids.player_id
        input_event_order = 0
        if not player_inputs or player_id == Consts.EMPTY_ID:
            return

        target_id = self._targeting_system.game_obj_targeting_dct[player_id].current_target_id
        spell_ids = self._controls_system.get_spell_ids_for_inputs(player_id, player_inputs, timestamp)

        for spell_id in spell_ids:
            input_event_order += 1
            yield UpcomingEvent(
                event_id=self._event_id_gen.generate_new_id(),
                timestamp=timestamp,
                source_id=player_id,
                spell_id=spell_id,
                target_id=target_id,
                priority=input_event_order,
            )

    def _create_environment_obj(self) -> None:
        obj_id: int = self._game_obj_id_gen.generate_new_id()

        self._active_obj_ids.add(obj_id)
        self._controls_system.create_environment_obj(obj_id)
        self._combat_system.create_environment_obj(obj_id)
        self._movement_system.create_environment_obj(obj_id)
        self._targeting_system.create_environment_obj(obj_id)
        self._vfx_and_sfx_system.create_environment_obj(obj_id)

        self._targeting_system.default_ids.environment_id = obj_id