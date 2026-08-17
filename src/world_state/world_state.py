from typing import Any, Iterable, Optional
from dataclasses import dataclass

from src.settings import Consts
from src.world_state import Controls, KeyPresses
from ._aura_handler import Aura, AuraHandler
from ._event_log import EventLog
from ._frame_heap import FrameHeap
from ._id_gen import IdGen
from ._event_system import UpcomingEvent, Outcome
from ._cooldown_system import CooldownSystem
from ._combat_system import CombatSystem
from ._movement_system import MovementSystem
from ._targeting_system import TargetingSystem
from ._vfx_and_sfx_system import VfxAndSfxSystem
from .systems_manager import SystemsManager



class WorldState:
    """ The entirely ECS-driven game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}

        self._systems_manager = SystemsManager()

    @property
    def view_obj_ids(self) -> Iterable[int]:
        return self._systems_manager.view_obj_ids

    @property
    def view_event_logs(self) -> dict[int, EventLog]:
        return self._event_log_for_each_frame

    def get_spell_ids_for_successful_events(self, timestamp: int) -> Iterable[int]:
        return self._event_log_for_each_frame[timestamp].get_successful_spell_ids

    def process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> None:
        for spell_id in setup_spell_ids:
            setup_event = UpcomingEvent(
                event_id=self._event_id_gen.generate_new_id(),
                timestamp=ingame_time,
                source_id=self._systems_manager.environment_id,
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
            f_event = self._finalize_event(u_event)
            self._process_event(f_event)
            event_log.log_event(f_event)
        self._event_log_for_each_frame[frame_end] = event_log

    def _finalize_event(self, u_event: UpcomingEvent) -> UpcomingEvent:
        target_id = self._systems_manager.decide_event_target(u_event.source_id, u_event.spell_id, u_event.target_id, u_event.is_aoe_targeting)
        outcome = self._systems_manager.decide_outcome(u_event.timestamp, u_event.source_id, u_event.spell_id, target_id, u_event.is_aoe_targeting)
        f_event = u_event.finalize_event(u_event.source_id, target_id, outcome)
        return f_event

    def _process_event(self, f_event: UpcomingEvent) -> None:
        timestamp = f_event.timestamp
        source_id = f_event.source_id
        target_id = f_event.target_id
        spell_id = f_event.spell_id
        if f_event.outcome_is_valid:
            new_obj_id = self._systems_manager.handle_spawn(timestamp, source_id, spell_id, target_id)
            for cascading_event in self._fetch_cascading_events(f_event, new_obj_id, source_id, spell_id, target_id):
                self._event_heap.insert_event(cascading_event)
            self._systems_manager.apply_event(timestamp, source_id, spell_id, target_id)

    def _fetch_cascading_events(self, u_event: UpcomingEvent, new_obj_id: int, source_id: int, spell_id: int, target_id: int) -> Iterable[UpcomingEvent]:

        # 1. Spawned Object Control Events
        if new_obj_id != Consts.EMPTY_ID:
            new_obj_target_id = self._systems_manager.get_current_target_for_obj(new_obj_id)

            scripted_spells = self._systems_manager._cooldown_system.get_scripted_spells(new_obj_id, u_event.timestamp)

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
        if self._systems_manager._targeting_system.is_area_of_effect(spell_id) and not u_event.is_aoe_targeting:
            target_ids = self._systems_manager.select_targets_for_aoe(source_id, target_id)
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
        sequenced_spells = self._systems_manager._targeting_system.get_spell_sequence(spell_id)
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

        # 4. Channel Tick Events
        if self._systems_manager._targeting_system.has_channel_start(spell_id):
            effect_id = self._systems_manager._targeting_system.get_periodic_effect(spell_id)
            priority = 0
            for tick_timestamp in self._systems_manager._targeting_system.get_tick_timestamps(u_event.timestamp, spell_id):
                priority += 1
                yield UpcomingEvent(
                    event_id=self._event_id_gen.generate_new_id(),
                    timestamp=tick_timestamp,
                    source_id=source_id,
                    spell_id=effect_id,
                    target_id=target_id,
                    priority=priority,
                )


    def _create_events_from_controls(self, player_inputs: list[str], timestamp: int) -> Iterable[UpcomingEvent]:
        player_id = self._systems_manager.player_id
        input_event_order = 0
        if not player_inputs or player_id == Consts.EMPTY_ID:
            return

        target_id = self._systems_manager.get_current_target_for_obj(self._systems_manager.player_id)
        spell_ids = self._systems_manager._cooldown_system.get_spell_ids_for_inputs(player_id, player_inputs, timestamp)

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