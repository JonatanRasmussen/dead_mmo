from src.models.aura import Aura
from src.models.spell import SpellTarget
from src.models.event import EventOutcome, UpcomingEvent, FinalizedEvent
from src.models.controls import Controls
from src.handlers.event_heap import EventHeap
from src.handlers.id_gen import IdGen
from src.handlers.event_log import EventLog
from src.controllers.world_state import WorldState


class EventFrame:
    def __init__(self, frame_start: float, frame_end: float, state: WorldState) -> None:
        self.frame_start: float = frame_start
        self.frame_end: float = frame_end
        self.state: WorldState = state
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._event_log: EventLog = EventLog()
        self._event_heap: EventHeap = EventHeap()

    def add_player_input(self, player_controls: Controls) -> None:
        self.state.add_player_controls(self.frame_end, player_controls)

    def process_frame(self) -> None:
        self._insert_frame_events_into_heap()
        while self._event_heap.has_unprocessed_events:
            event = self._event_heap.pop_next_event()
            f_event = self._finalize_event(event)
            self._event_log.log_event(f_event)
            if f_event.outcome_is_valid:
                self.state.let_event_modify_world_state(f_event)
                if f_event.spell.has_cascading_events:
                    self._insert_cascading_events_into_heap(f_event)

    def _insert_frame_events_into_heap(self) -> None:
        # Add setup event if state is not initialized
        if IdGen.is_empty_id(self.state.important_ids.player_id):
            setup_event = UpcomingEvent(
                event_id=self._generate_new_event_id(),
                timestamp=0.0,
                spell_id=self.state.important_ids.setup_spell_id,
            )
            self._event_heap.insert_event(setup_event)
        # Add events from periodic auras ticking this frame
        for aura in self.state.view_auras:
            if not aura.is_expired(self.frame_start):
                self._insert_periodic_events_into_heap(aura)
        # Add events from controls (game inputs) happening this frame
        self._insert_controls_events_into_heap()

    def _insert_periodic_events_into_heap(self, aura: Aura) -> None:
        tick_timestamps = aura.get_timestamps_for_ticks_this_frame(self.frame_start, self.frame_end)
        for timestamp in tick_timestamps:
            event_id=self._generate_new_event_id()
            aura_tick = UpcomingEvent.create_from_aura_tick(event_id, timestamp, aura)
            self._event_heap.insert_event(aura_tick)

    def _insert_controls_events_into_heap(self) -> None:
        controls_this_frame = self.state.view_controls_for_current_frame(self.frame_start, self.frame_end)
        for timestamp, obj_id, controls in controls_this_frame:
            if timestamp == self.frame_start and timestamp > 0.0:
                continue  # Prevent double processing of controls
            source_obj = self.state.get_game_obj(obj_id)
            spell_ids = source_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                controls_event = UpcomingEvent(
                    event_id=self._generate_new_event_id(),
                    timestamp=timestamp,
                    source_id=source_obj.obj_id,
                    spell_id=spell_id,
                    target_id=source_obj.current_target,
                )
                self._event_heap.insert_event(controls_event)

    def _insert_cascading_events_into_heap(self, f_event: FinalizedEvent) -> None:
        # If the event's spell is area-of-effect, add new events for each target
        if f_event.spell.is_area_of_effect:
            target_ids = SpellTarget.handle_aoe(f_event.source, f_event.target, self.state.view_game_objs)
            for target_id in target_ids:
                new_event_id = self._generate_new_event_id()
                new_event = f_event.upcoming_event.also_target(new_event_id, f_event.spell_id, target_id)
                self._event_heap.insert_event(new_event)

        # If the event's spell cascades into new spells, add those as new events
        if f_event.spell.spell_sequence is not None:
            for next_spell in f_event.spell.spell_sequence:
                new_event_id = self._generate_new_event_id()
                sequence_event = f_event.upcoming_event.continue_spell_sequence(new_event_id, next_spell)
                self._event_heap.insert_event(sequence_event)

        # If an aura was just created, see if it has any ticks happening this frame
        if f_event.spell.has_aura_apply:
            aura = self.state.get_aura(f_event.source_id, f_event.spell_id, f_event.target_id)
            self._insert_periodic_events_into_heap(aura)

    def _finalize_event(self, event: UpcomingEvent) -> FinalizedEvent:
        # Convert source_id/spell_id/target_id to actual object references
        # Finalize the event's source_obj
        if IdGen.is_valid_id(event.source_id):
            source_id = event.source_id
        else:
            source_id = self.state.important_ids.environment_id
        source_obj = self.state.get_game_obj(source_id)

        # Finalize the event's spell
        spell = self.state.get_spell(event.spell_id)

        # Finalize the event's target_obj
        target_id = spell.targeting.select_target(source_obj, event.target_id, self.state.important_ids)
        if target_id == source_obj.obj_id:
            target_obj = source_obj
        else:
            target_obj = self.state.get_game_obj(target_id)

        # Finalize the event's outcome and update its source and target
        updated_event = event.update_source_and_target(source_obj.obj_id, target_obj.obj_id)
        if updated_event.is_aura_tick and not self.state.aura_exists(event):  # Do NOT use updated_event here
            outcome = EventOutcome.AURA_NO_LONGER_EXISTS
        else:
            outcome = EventOutcome.decide_outcome(event.timestamp, source_obj, spell, target_obj)
        finalized_event = FinalizedEvent(
            source=source_obj,
            spell=spell,
            target=target_obj,
            upcoming_event=updated_event,
            outcome=outcome,
        )
        return finalized_event

    def _generate_new_event_id(self) -> int:
        return self._event_id_gen.generate_new_id()
