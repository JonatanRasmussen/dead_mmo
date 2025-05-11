from typing import Dict, List, Tuple, ValuesView

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


class EventCreator:
    """ A class that handles CombatEvents. """

    @staticmethod
    def create_events_happening_this_frame(state: WorldState) -> List['CombatEvent']:
        frame_events: List[CombatEvent] = []
        if not state.has_been_initialized:
            frame_events.append(EventCreator._create_setup_event(state))
        frame_events.extend(EventCreator._create_aura_events(state))
        frame_events.extend(EventCreator._create_controls_events(state))
        return frame_events

    @staticmethod
    def create_cascading_events(spell: Spell, event: 'CombatEvent', state: WorldState) -> List['CombatEvent']:
        frame_events: List[CombatEvent] = []
        frame_events.extend(EventCreator._create_spell_sequence_events(spell, event, state))
        frame_events.extend(EventCreator._create_events_from_aura(spell, event, state))
        return frame_events


    @staticmethod
    def _create_aura_events(state: WorldState) -> List['CombatEvent']:
        events: List['CombatEvent'] = []
        for aura in state.all_auras:
            if aura.has_tick_this_frame(state.previous_timestamp, state.current_timestamp):
                events.append(EventCreator._create_from_aura_tick(state, aura))
        return events

    @staticmethod
    def _create_controls_events(state: WorldState) -> List['CombatEvent']:
        events: List['CombatEvent'] = []
        for timestamp, obj_id, controls in state.all_controls_in_current_frame:
            if timestamp == state.previous_timestamp:
                continue  # Prevent double processing of controls
            source_obj: GameObj = state.get_game_obj(obj_id)
            spell_ids = source_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                events.append(EventCreator._create_controls_event(state, timestamp, source_obj, spell_id))
        return events

    @staticmethod
    def _create_spell_sequence_events(spell: Spell, event: 'CombatEvent', state: WorldState) -> List['CombatEvent']:
        events: List['CombatEvent'] = []
        if spell.spell_sequence is not None:
            for next_spell in spell.spell_sequence:
                events.append(event.continue_spell_sequence(state.generate_new_event_id(), next_spell))
        return events

    @staticmethod
    def _create_events_from_aura(spell: Spell, event: 'CombatEvent', state: WorldState) -> List['CombatEvent']:
        events: List['CombatEvent'] = []
        if spell.flags & SpellFlag.AURA:
            aura = state.get_aura(event.source, event.spell, event.target)
            if aura.has_tick_this_frame(state.previous_timestamp, state.current_timestamp):
                events.append(EventCreator._create_from_aura_tick(state, aura))
        return events

    @staticmethod
    def _create_from_aura_tick(state: WorldState, aura: Aura) -> 'CombatEvent':
        return CombatEvent(
            event_id=state.generate_new_event_id(),
            timestamp=state.current_timestamp,
            source=aura.source_id,
            spell=aura.spell_id,
            target=aura.target_id,
            is_periodic_tick=True,
        )

    @staticmethod
    def _create_setup_event(state: WorldState) -> 'CombatEvent':
        return CombatEvent(
            event_id=state.generate_new_event_id(),
            timestamp=0.0,
            source=state.environment_id,
            spell=state.setup_spell_id,
        )

    @staticmethod
    def _create_controls_event(state: WorldState, timestamp: float, source: GameObj, spell_id: int) -> 'CombatEvent':
        return CombatEvent(
            event_id=state.generate_new_event_id(),
            timestamp=timestamp,
            source=source.obj_id,
            spell=spell_id,
            target=source.current_target,
        )
