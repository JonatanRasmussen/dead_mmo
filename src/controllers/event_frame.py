from typing import Iterable, Optional
from src.config import Consts
from src.models import Aura, Controls, GameObj, SpellTarget, EventOutcome, UpcomingEvent, FinalizedEvent
from src.handlers import EventHeap, IdGen, EventLog
from src.controllers.world_state import WorldState


class EventFrame:
    def __init__(self, frame_start: float, frame_end: float, state: WorldState) -> None:
        self.event_log: EventLog = EventLog(frame_start, frame_end)
        self._frame_start: float = frame_start
        self._frame_end: float = frame_end
        self._state: WorldState = state

    @staticmethod
    def update_state(frame_start: float, frame_end: float, state: WorldState) -> EventLog:
        frame = EventFrame(frame_start, frame_end, state)
        frame.process_frame()
        return frame.event_log

    def process_frame(self) -> None:
        event_id_gen = IdGen.create_preassigned_range(1, 10_000)
        event_heap = EventHeap()
        for event in self._get_initial_frame_events():
            event_heap.insert_event(event)

        while event_heap.has_unprocessed_events:
            upcoming_event = event_heap.pop_next_event()
            finalized_event = self._finalize_event(upcoming_event, event_id_gen.generate_new_id())
            self.event_log.log_event(finalized_event)
            if finalized_event.outcome_is_valid:
                new_obj = self._state.let_event_spawn_new_obj(finalized_event)
                self._state.let_event_modify_aura(finalized_event)
                if finalized_event.spell.has_cascading_events:
                    for cascading_event in self._get_cascading_events(finalized_event, new_obj):
                        assert (cascading_event.timestamp > self._frame_start or cascading_event.timestamp == 0.0), f"frame starts at {self._frame_start} but event has timestamp {cascading_event}."
                        assert cascading_event.timestamp <= self._frame_end, f"frame ends at {self._frame_end}, but event has timestamp {cascading_event}."
                        event_heap.insert_event(cascading_event)
                self._state.let_event_modify_game_obj(finalized_event)
        self._state.remove_all_expired_auras(self._frame_end)

    def _get_initial_frame_events(self) -> Iterable[UpcomingEvent]:
        # Add setup event if state is not initialized
        if Consts.is_empty_id(self._state.important_ids.player_id):
            yield UpcomingEvent(
                timestamp=0.0,
                spell_id=self._state.important_ids.setup_spell_id,
            )

        # Add events from auras (periodic spell effects) ticking this frame
        for aura in self._state.view_auras:
            yield from aura.create_aura_tick_events(self._frame_start, self._frame_end)

        # Add events from controls (i.e. game inputs) happening this frame
        for _, obj_id, controls in self._state.view_controls_for_current_frame(self._frame_start, self._frame_end):
            assert (controls.ingame_timestamp > self._frame_start or controls.ingame_timestamp == 0.0), f"frame starts at {self._frame_start} but controls has timestamp {controls}."
            assert controls.ingame_timestamp <= self._frame_end, f"frame ends at {self._frame_end}, but controls has timestamp {controls}."
            game_obj = self._state.get_game_obj(obj_id)
            yield from game_obj.create_events_from_controls(controls, self._frame_start, self._frame_end)

    def _get_cascading_events(self, f_event: FinalizedEvent, new_obj: Optional[GameObj]) -> Iterable[UpcomingEvent]:
        # If the event's spell spawned an obj, add any new controls happening this frame
        if new_obj is not None and f_event.spell.obj_controls is not None:
            assert f_event.spell.has_spawned_object, "new_obj exists but is not from spell."
            for controls in f_event.spell.obj_controls:
                assert (new_obj.spawn_timestamp > self._frame_start or new_obj.spawn_timestamp == 0.0), f"frame starts at {self._frame_start} but {new_obj.obj_id} has spawn_timestamp {new_obj.spawn_timestamp}."
                assert new_obj.spawn_timestamp <= self._frame_end, f"frame ends at {self._frame_end} but {new_obj.obj_id} has spawn_timestamp {new_obj.spawn_timestamp}."
                offset_controls = controls.increase_offset(new_obj.spawn_timestamp)
                assert not offset_controls.is_empty, f"Controls for {new_obj.obj_id} is empty."
                yield from new_obj.create_events_from_controls(offset_controls, self._frame_start, self._frame_end)

        # If the event's spell is area-of-effect, add new events for each target
        if f_event.spell.is_area_of_effect:
            target_ids = SpellTarget.handle_aoe(f_event.source, f_event.target, self._state.view_game_objs)
            for target_id in target_ids:
                yield f_event.upcoming_event.also_target(f_event.spell_id, target_id)

        # If the event's spell cascades into new spells, add those as new events
        if f_event.spell.spell_sequence is not None:
            for next_spell in f_event.spell.spell_sequence:
                yield f_event.upcoming_event.continue_spell_sequence(next_spell)

        # If an aura was just created, see if it has any ticks happening this frame
        if f_event.spell.has_aura_apply:
            aura = self._state.get_aura(f_event.source_id, f_event.spell_id, f_event.target_id)
            yield from aura.create_aura_tick_events(self._frame_start, self._frame_end)

    def _finalize_event(self, event: UpcomingEvent, event_id: int) -> FinalizedEvent:
        # Convert source_id/spell_id/target_id to actual object references
        # Finalize the event's source_obj
        assert (event.timestamp > self._frame_start or event.timestamp == 0.0), f"frame starts at {self._frame_start} but event has timestamp {event}."
        assert event.timestamp <= self._frame_end, f"frame ends at {self._frame_end}, but event has timestamp {event}."
        if Consts.is_valid_id(event.source_id):
            source_id = event.source_id
        else:
            source_id = self._state.important_ids.environment_id
        source_obj = self._state.get_game_obj(source_id)

        # Finalize the event's spell
        spell = self._state.get_spell(event.spell_id)

        # Finalize the event's target_obj
        target_id = spell.targeting.select_target(source_obj, event.target_id, self._state.important_ids)
        if target_id == source_obj.obj_id:
            target_obj = source_obj
        else:
            if spell.is_target_of_target and Consts.is_valid_id(target_id):
                obj_with_target_to_copy = self._state.get_game_obj(target_id)
                if Consts.is_valid_id(obj_with_target_to_copy.current_target):
                    target_id = obj_with_target_to_copy.current_target
                else:
                    target_id = self._state.important_ids.missing_target_id
            target_obj = self._state.get_game_obj(target_id)

        # Finalize the event's outcome and update its source and target
        updated_event = event.update_source_and_target(source_obj.obj_id, target_obj.obj_id)
        if updated_event.is_aura_tick and not self._state.aura_exists(event):  # Do NOT use updated_event here
            outcome = EventOutcome.AURA_NO_LONGER_EXISTS
        else:
            outcome = EventOutcome.decide_outcome(event.timestamp, source_obj, spell, target_obj)
        finalized_event = FinalizedEvent(
            event_id=event_id,
            source=source_obj,
            spell=spell,
            target=target_obj,
            upcoming_event=updated_event,
            outcome=outcome,
        )
        return finalized_event