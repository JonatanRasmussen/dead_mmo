from typing import NamedTuple, List
from enum import Enum

from src.models.id_gen import IdGen
from src.models.aura import Aura
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.world_state import WorldState


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = 1
    FAILED = 2
    MISSED = 3


class CombatEvent(NamedTuple):
    event_id: int = IdGen.EMPTY_ID
    base_event: int = IdGen.EMPTY_ID
    timestamp: float = 0.0
    source: int = IdGen.EMPTY_ID
    spell: int = IdGen.EMPTY_ID
    target: int = IdGen.EMPTY_ID
    is_periodic_tick: bool = False
    outcome: EventOutcome = EventOutcome.EMPTY

    @staticmethod
    def create_events_happening_this_frame(state: WorldState) -> List['CombatEvent']:
        frame_events: List[CombatEvent] = []
        if not state.has_been_initialized:
            frame_events.append(CombatEvent._create_setup_event(state))
        frame_events.extend(CombatEvent._create_aura_events(state))
        frame_events.extend(CombatEvent._create_controls_events(state))
        return frame_events

    @staticmethod
    def create_cascading_events(spell: Spell, event: 'CombatEvent', state: WorldState) -> List['CombatEvent']:
        frame_events: List[CombatEvent] = []
        frame_events.extend(CombatEvent._create_spell_sequence_events(spell, event, state))
        frame_events.extend(CombatEvent._create_events_from_aura(spell, event, state))
        return frame_events

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] (obj_{self.source:04d} uses spell_{self.spell:04d} on obj_{self.target:04d}.)"

    @property
    def outcome_is_valid(self) -> bool:
        return self.outcome != EventOutcome.FAILED

    @property
    def is_subevent(self) -> bool:
        return not IdGen.is_empty_id(self.base_event)

    @property
    def is_aoe(self) -> bool:
        return False #fix later

    @property
    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.target)

    def update_target(self, new_target: int) -> 'CombatEvent':
        return self._replace(target=new_target)

    def finalize_outcome(self, new_outcome: EventOutcome) -> 'CombatEvent':
        return self._replace(outcome=new_outcome)

    def continue_spell_sequence(self, new_event_id: int, new_spell_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, spell=new_spell_id)

    def also_target(self, new_event_id: int, new_target_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, target=new_target_id)

    @classmethod
    def _create_from_aura_tick(cls, state: WorldState, aura: Aura) -> 'CombatEvent':
        return CombatEvent(
            event_id=state.generate_new_event_id(),
            timestamp=state.current_timestamp,
            source=aura.source_id,
            spell=aura.spell_id,
            target=aura.target_id,
            is_periodic_tick=True,
        )

    @classmethod
    def _create_setup_event(cls, state: WorldState) -> 'CombatEvent':
        return CombatEvent(
            event_id=state.generate_new_event_id(),
            timestamp=0.0,
            source=state.environment_id,
            spell=state.setup_spell_id,
        )

    @staticmethod
    def _create_aura_events(state: WorldState) -> List['CombatEvent']:
        events: List['CombatEvent'] = []
        for aura in state.all_auras:
            if aura.has_tick_this_frame(state.previous_timestamp, state.current_timestamp):
                events.append(CombatEvent._create_from_aura_tick(state, aura))
        return events

    @staticmethod
    def _create_controls_events(state: WorldState) -> List['CombatEvent']:
        events: List['CombatEvent'] = []
        for timestamp, obj_id, controls in state.all_controls_in_current_frame:
            if timestamp == state.previous_timestamp:
                continue  # Prevent double processing of controls
            game_obj: GameObj = state.get_game_obj(obj_id)
            current_target = game_obj.current_target
            spell_ids = game_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                events.append(CombatEvent(
                    event_id=state.generate_new_event_id(),
                    timestamp=timestamp,
                    source=obj_id,
                    spell=spell_id,
                    target=current_target,
                ))
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
                events.append(CombatEvent._create_from_aura_tick(state, aura))
        return events
