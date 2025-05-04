from typing import Dict, List, Tuple, ValuesView
import heapq

from src.models.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import Spell
from src.models.combat_event import CombatEvent
from src.models.world_state import WorldState
from src.handlers.spell_handler import SpellHandler
from src.handlers.spell_validator import SpellValidator


class EventSystem:
    """ A class that handles CombatEvents. """
    def __init__(self) -> None:
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._event_heap: List[Tuple[float, int, int, CombatEvent]] = []
        self._event_log: Dict[int, CombatEvent] = {}

    def setup_game(self, setup_spell_id: int, state: WorldState) -> None:
        event_id = self._get_new_id()
        initial_timestamp = 0.0
        source = state.environment.obj_id
        setup_event = CombatEvent.create_setup_event(event_id, initial_timestamp, source, setup_spell_id)
        self._register_event(setup_event)
        self.process_events_happening_this_frame(state)

    def process_events_happening_this_frame(self, state: WorldState) -> None:
        max_iterations = 10_000
        while self._has_unprocessed_events:
            assert max_iterations > 0, "Infinite loop detected."
            max_iterations -= 1
            event = self._get_next_event()
            self._process_event(event, state)

    def find_events_happening_this_frame(self, world_state: WorldState) -> None:
        assert not self._has_unprocessed_events, "Event heap is not empty. This should not happen."
        self._event_heap.clear()
        self._register_events_from_periodic_auras(world_state)
        self._register_events_from_controls(world_state)

    @property
    def _has_unprocessed_events(self) -> float:
        return len(self._event_heap) > 0

    def _get_new_id(self) -> int:
        return self._event_id_gen.new_id()

    def _get_next_event(self) -> CombatEvent:
        _, _, _, event = heapq.heappop(self._event_heap)
        return event

    def _process_event(self, event: CombatEvent, state: WorldState) -> None:
        # Convert source_id/spell_id/target_id to actual object references
        source_obj = state.get_game_obj(event.source)
        spell = state.spell_database.get_spell(event.spell)
        target_obj = SpellHandler.select_target(event, source_obj, spell, state)
        updated_event = event.update_target(target_obj.obj_id)
        outcome = SpellValidator.decide_outcome(source_obj, spell, target_obj)
        finalized_event = updated_event.finalize_outcome(outcome)
        self._log_event(finalized_event)
        if finalized_event.outcome_is_valid:
            self._register_events_from_spell_sequence(spell, finalized_event)
            SpellHandler.handle_spell(source_obj, spell, target_obj, state)

    def _log_event(self, event: CombatEvent):
        if not event.outcome_is_valid:
            print("Currently, this should never happen.")
        if event.outcome_is_valid:
            self._event_log[event.event_id] = event
            print(event.event_summary)

    def _register_event(self, event: CombatEvent) -> None:
        heapq.heappush(self._event_heap, (event.timestamp, event.source, event.event_id, event))

    def _register_events_from_spell_sequence(self, spell: Spell, event: CombatEvent) -> None:
        if spell.spell_sequence is not None:
            for next_spell in spell.spell_sequence:
                continued_event = event.continue_spell_sequence(self._get_new_id(), next_spell)
                self._register_event(continued_event)

    def _register_events_from_periodic_auras(self, state: WorldState) -> None:
        for aura in state.auras.values():
            if aura.has_tick_this_frame(state.previous_timestamp, state.current_timestamp):
                event = CombatEvent.create_from_aura_tick(self._get_new_id(), state.current_timestamp, aura)
                self._register_event(event)

    def _register_events_from_controls(self, world_state: WorldState) -> None:
        start_key: Tuple[float, int] = (world_state.previous_timestamp, min(world_state.game_objs.keys()))
        end_key: Tuple[float, int] = (world_state.current_timestamp, max(world_state.game_objs.keys()))
        for timestamp, obj_id in world_state.controls.irange(start_key, end_key):
            if timestamp == world_state.previous_timestamp:
                continue # Prevent double processing of controls
            controls: Controls = world_state.controls[(timestamp, obj_id)]
            game_obj: GameObj = world_state.get_game_obj(obj_id)
            current_target = game_obj.current_target
            spell_ids = game_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                event = CombatEvent.create_from_controls(self._get_new_id(), controls.timestamp, obj_id, spell_id, current_target)
                self._register_event(event)
