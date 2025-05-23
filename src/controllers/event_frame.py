import heapq
from typing import Dict, List, Tuple, ValuesView

from src.models.aura import Aura
from src.models.event import UpcomingEvent, FinalizedEvent
from src.models.controls import Controls
from src.handlers.event_heap import EventHeap
from src.handlers.id_gen import IdGen
from src.controllers.world_state import WorldState
from src.utils.spell_validation import SpellValidation
from src.utils.target_selection import TargetSelection


class EventFrame:
    def __init__(self, frame_start: float, frame_end: float, state: WorldState) -> None:
        self.frame_start: float = frame_start
        self.frame_end: float = frame_end
        self.state = state
        self._event_heap: EventHeap = EventHeap()

    def add_player_input(self, player_controls: Controls) -> None:
        self.state.add_player_controls(self.frame_end, player_controls)

    def process_frame(self) -> None:
        self._insert_frame_events_into_heap()
        while self._event_heap.has_unprocessed_events:
            event = self._event_heap.pop_next_event()
            f_event = self._finalize_event(event)
            if f_event.outcome_is_valid:
                self.state.let_event_modify_world_state(f_event)
                if f_event.spell.has_cascading_events:
                    self._insert_cascading_events_into_heap(f_event)

    def _insert_frame_events_into_heap(self) -> None:
        # Add setup event if state is not initialized
        if IdGen.is_empty_id(self.state.important_ids.player_id):
            setup_event = UpcomingEvent(
                event_id=self.state.generate_new_event_id(),
                timestamp=0.0,
                spell=self.state.important_ids.setup_spell_id,
            )
            self._event_heap.insert_event(setup_event)
        # Add events from periodic auras ticking this frame
        for aura in self.state.view_auras:
            self._insert_periodic_events_into_heap(aura)
        # Add events from controls (game inputs) happening this frame
        self._insert_controls_events_into_heap()

    def _insert_periodic_events_into_heap(self, aura: Aura) -> None:
        tick_timestamps = aura.get_timestamps_for_ticks_this_frame(self.frame_start, self.frame_end)
        for timestamp in tick_timestamps:
            aura_tick = UpcomingEvent(
                event_id=self.state.generate_new_event_id(),
                timestamp=timestamp,
                source=aura.source_id,
                spell=aura.aura_effect_id,
                target=aura.target_id,
                is_periodic_tick=True,
            )
            self._event_heap.insert_event(aura_tick)

    def _insert_controls_events_into_heap(self) -> None:
        controls_this_frame = self.state.view_controls_for_current_frame(self.frame_start, self.frame_end)
        for timestamp, obj_id, controls in controls_this_frame:
            if timestamp == self.frame_start:
                continue  # Prevent double processing of controls
            source_obj = self.state.get_game_obj(obj_id)
            spell_ids = source_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                controls_event = UpcomingEvent(
                    event_id=self.state.generate_new_event_id(),
                    timestamp=timestamp,
                    source=source_obj.obj_id,
                    spell=spell_id,
                    target=source_obj.current_target,
                )
                self._event_heap.insert_event(controls_event)

    def _insert_cascading_events_into_heap(self, f_event: FinalizedEvent) -> None:
        # If the event's spell is area-of-effect, add new events for each target
        if f_event.spell.is_aoe:
            target_ids = TargetSelection.handle_aoe(f_event.source, f_event.spell,f_event.target, self.state.view_game_objs)
            for target_id in target_ids:
                new_event_id = self.state.generate_new_event_id()
                spell_effect = f_event.spell.effect_id
                new_event = f_event.pending_event.also_target(new_event_id, spell_effect, target_id)
                self._event_heap.insert_event(new_event)

        # If the event's spell cascades into new spells, add those as new events
        if f_event.spell.spell_sequence is not None:
            for next_spell in f_event.spell.spell_sequence:
                new_event_id = self.state.generate_new_event_id()
                sequence_event = f_event.pending_event.continue_spell_sequence(new_event_id, next_spell)
                self._event_heap.insert_event(sequence_event)

        # If an aura was just created, see if it has any ticks happening this frame
        if f_event.spell.has_aura_apply:
            aura = self.state.get_aura(f_event.source_id, f_event.spell_id, f_event.target_id)
            self._insert_periodic_events_into_heap(aura)

    def _finalize_event(self, event: UpcomingEvent) -> FinalizedEvent:
        # Convert source_id/spell_id/target_id to actual object references
        if IdGen.is_valid_id(event.source):
            source_id = event.source
        else:
            source_id = self.state.important_ids.environment_id
        source_obj = self.state.get_game_obj(source_id)
        spell = self.state.get_spell(event.spell)
        target_id = TargetSelection.select_target(source_obj, spell, event.target, self.state.important_ids)
        if target_id == source_obj.obj_id:
            target_obj = source_obj
        else:
            target_obj = self.state.get_game_obj(target_id)
        updated_event = event.update_source_and_target(source_obj.obj_id, target_obj.obj_id)
        outcome = SpellValidation.decide_outcome(event.timestamp, source_obj, spell, target_obj)
        finalized_event = FinalizedEvent(
            source=source_obj,
            spell=spell,
            target=target_obj,
            pending_event=updated_event,
            outcome=outcome,
        )
        return finalized_event