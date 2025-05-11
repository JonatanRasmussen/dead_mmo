from typing import Dict, List, Tuple, ValuesView

from src.models.id_gen import IdGen
from src.models.aura import Aura
from src.models.controls import Controls
from src.models.event_heap import EventHeap
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import CombatEvent
from src.models.world_state import WorldState
from src.handlers.event_creator import EventCreator
from src.handlers.spell_handler import SpellHandler
from src.handlers.spell_validator import SpellValidator


class EventSystem:
    """ A class that handles CombatEvents. """

    @staticmethod
    def process_frame(state: WorldState) -> Dict[int, CombatEvent]:
        frame_event_log: Dict[int, CombatEvent] = {}
        frame_events = EventCreator.create_events_happening_this_frame(state)
        event_heap = EventHeap.create_from_event_list(frame_events)
        while event_heap.has_unprocessed_events:
            event = event_heap.get_next_event()
            spell = state.spell_database.get_spell(event.spell)
            finalized_event = EventSystem._process_event(spell, event, state)
            if finalized_event.outcome_is_valid and spell.has_cascading_events:
                cascading_events = EventCreator.create_cascading_events(spell, event, state)
                event_heap.register_multiple_events(cascading_events)
            frame_event_log[event.event_id] = finalized_event
        return frame_event_log

    @staticmethod
    def _process_event(spell: Spell, event: CombatEvent, state: WorldState) -> CombatEvent:
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
