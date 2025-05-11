from typing import Dict, List, Tuple, ValuesView
import heapq

from src.models.id_gen import IdGen
from src.models.aura import Aura
from src.models.controls import Controls
from src.models.event_heap import EventHeap
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import CombatEvent
from src.models.world_state import WorldState
from src.handlers.spell_handler import SpellHandler
from src.handlers.spell_validator import SpellValidator


class EventSystem:
    """ A class that handles CombatEvents. """
    def __init__(self) -> None:
        self._event_heap: List[Tuple[float, int, int, CombatEvent]] = []
        self._event_log: Dict[int, CombatEvent] = {}

    @staticmethod
    def process_frame(state: WorldState) -> Dict[int, CombatEvent]:
        frame_event_log: Dict[int, CombatEvent] = {}
        frame_events = CombatEvent.create_events_happening_this_frame(state)
        event_heap = EventHeap.create_from_event_list(frame_events)
        while event_heap.has_unprocessed_events:
            event = event_heap.get_next_event()
            spell = state.spell_database.get_spell(event.spell)
            finalized_event = EventSystem.process_event(spell, event, state)
            if finalized_event.outcome_is_valid and spell.has_cascading_events:
                cascading_events = CombatEvent.create_cascading_events(spell, event, state)
                event_heap.register_multiple_events(cascading_events)
            frame_event_log[event.event_id] = event
        return frame_event_log

    @staticmethod
    def process_event(spell: Spell, event: CombatEvent, state: WorldState) -> CombatEvent:
        # Convert source_id/spell_id/target_id to actual object references
        spell = state.spell_database.get_spell(event.spell)
        source_obj = state.get_game_obj(event.source)
        target_obj = SpellHandler.select_target(event, source_obj, spell, state)
        updated_event = event.update_target(target_obj.obj_id)
        outcome = SpellValidator.decide_outcome(source_obj, spell, target_obj)
        finalized_event = updated_event.finalize_outcome(outcome)
        if finalized_event.outcome_is_valid:
            SpellHandler.handle_spell(source_obj, spell, target_obj, state)
        return finalized_event


    def process_events_happening_this_frame(self, state: WorldState) -> None:
        self._find_events_happening_this_frame(state)
        max_iterations = 100_000
        while self._has_unprocessed_events:
            assert max_iterations > 0, f"Event limit of {max_iterations} reached, infinite loop detected."
            max_iterations -= 1
            event = self._get_next_event()
            self._process_event(event, state)

    def _find_events_happening_this_frame(self, state: WorldState) -> None:
        assert not self._has_unprocessed_events, "Event heap is not empty. This should not happen."
        self._event_heap.clear()
        self._try_register_initialization_event(state)
        for aura in state.all_auras:
            self._register_events_from_periodic_aura(aura, state)
        self._register_events_from_controls(state)

    @property
    def _has_unprocessed_events(self) -> float:
        return len(self._event_heap) > 0

    def _get_next_event(self) -> CombatEvent:
        _, _, _, event = heapq.heappop(self._event_heap)
        return event

    def _process_event(self, event: CombatEvent, state: WorldState) -> None:
        # Convert source_id/spell_id/target_id to actual object references
        spell = state.spell_database.get_spell(event.spell)
        source_obj = state.get_game_obj(event.source)
        target_obj = SpellHandler.select_target(event, source_obj, spell, state)
        updated_event = event.update_target(target_obj.obj_id)
        outcome = SpellValidator.decide_outcome(source_obj, spell, target_obj)
        finalized_event = updated_event.finalize_outcome(outcome)
        self._log_event(finalized_event)
        if finalized_event.outcome_is_valid:
            self._register_events_from_spell_sequence(spell, finalized_event, state)
            SpellHandler.handle_spell(source_obj, spell, target_obj, state)
            if spell.flags & SpellFlag.AURA:
                aura = state.get_aura(source_obj.obj_id, spell.spell_id, target_obj.obj_id)
                self._register_events_from_periodic_aura(aura, state)

    def _log_event(self, event: CombatEvent):
        if not event.outcome_is_valid:
            print("Currently, this should never happen.")
        if event.outcome_is_valid:
            self._event_log[event.event_id] = event
            print(event.event_summary)

    def _register_event(self, event: CombatEvent) -> None:
        heapq.heappush(self._event_heap, (event.timestamp, event.source, event.event_id, event))

    def _register_events_from_spell_sequence(self, spell: Spell, event: CombatEvent, state: WorldState) -> None:
        if spell.spell_sequence is not None:
            for next_spell in spell.spell_sequence:
                continued_event = event.continue_spell_sequence(state.generate_new_event_id(), next_spell)
                self._register_event(continued_event)

    def _try_register_initialization_event(self, state: WorldState) -> None:
        if not state.has_been_initialized:
            setup_event = CombatEvent._create_setup_event(state)
            self._register_event(setup_event)

    def _register_events_from_periodic_aura(self, aura: Aura, state: WorldState) -> None:
        if aura.has_tick_this_frame(state.previous_timestamp, state.current_timestamp):
            event = CombatEvent._create_from_aura_tick(state, aura)
            self._register_event(event)

    def _register_events_from_controls(self, state: WorldState) -> None:
        for timestamp, obj_id, controls in state.get_controls_in_timerange(state.previous_timestamp, state.current_timestamp):
            if timestamp == state.previous_timestamp:
                continue  # Prevent double processing of controls
            game_obj: GameObj = state.get_game_obj(obj_id)
            current_target = game_obj.current_target
            spell_ids = game_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                event = CombatEvent(
                    event_id=state.generate_new_event_id(),
                    timestamp=timestamp,
                    source=obj_id,
                    spell=spell_id,
                    target=current_target
                )
                self._register_event(event)
