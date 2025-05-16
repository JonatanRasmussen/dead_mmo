import heapq
from typing import Dict, List, Tuple, ValuesView

from src.models.combat_event import CombatEvent, FinalizedEvent
from src.handlers.event_heap import EventHeap
from src.controller.world_state import WorldState
from src.utils.frame_events import FrameEvents
from src.utils.spell_handler import SpellHandler
from src.utils.spell_validator import SpellValidator


class FrameProcessor:

    @staticmethod
    def process_frame(state: WorldState) -> None:
        events_this_frame = FrameEvents.create_events_happening_this_frame(state)
        event_heap = EventHeap.create_heap_from_list_of_events(events_this_frame)
        while event_heap.has_unprocessed_events:
            event = event_heap.get_next_event()
            f_event = FrameProcessor._finalize_event(event, state)
            if f_event.outcome_is_valid:
                state.let_event_modify_world_state(f_event)
                if f_event.outcome_is_valid and f_event.spell.has_cascading_events:
                    cascading_events = FrameProcessor._create_cascading_events(f_event, state)
                    event_heap.register_events(cascading_events)

    @staticmethod
    def _finalize_event(event: CombatEvent, state: WorldState) -> FinalizedEvent:
        # Convert source_id/spell_id/target_id to actual object references
        source_obj = state.get_game_obj(event.source)
        spell = state.get_spell(event.spell)
        target_id = SpellHandler.select_target(source_obj, spell, event.target, state.important_ids)
        if target_id == source_obj.obj_id:
            target_obj = source_obj
        else:
            target_obj = state.get_game_obj(target_id)
        updated_event = event.update_target(target_obj.obj_id)
        outcome = SpellValidator.decide_outcome(source_obj, spell, target_obj)
        finalized_event = FinalizedEvent(
            source=source_obj,
            spell=spell,
            target=target_obj,
            combat_event=updated_event,
            outcome=outcome,
        )
        return finalized_event

    @staticmethod
    def _create_cascading_events(f_event: FinalizedEvent, state: WorldState) -> List[CombatEvent]:
        cascading_events: List[CombatEvent] = []

        # If the event's spell cascades into new spells, add those as new events
        if f_event.spell.spell_sequence is not None:
            for next_spell in f_event.spell.spell_sequence:
                new_event_id = state.generate_new_event_id()
                new_event = f_event.combat_event.continue_spell_sequence(new_event_id, next_spell)
                cascading_events.append(new_event)

        # If an aura was just created, see if it has any ticks happening this frame
        if f_event.spell.has_aura_apply:
            aura = state.get_aura(f_event.source_id, f_event.spell_id, f_event.target_id)
            aura_tick_events = FrameEvents.create_periodic_events_this_frame(aura, state)
            cascading_events.extend(aura_tick_events)

        return cascading_events