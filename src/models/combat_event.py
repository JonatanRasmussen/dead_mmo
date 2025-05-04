from typing import NamedTuple
from enum import Enum

from src.models.id_gen import IdGen
from src.models.aura import Aura


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

    @classmethod
    def create_from_aura_tick(cls, event_id: int, timestamp: float, aura: Aura) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=aura.source_id,
            spell=aura.spell_id,
            target=aura.target_id,
            is_periodic_tick=True,
        )

    @classmethod
    def create_from_controls(cls, event_id: int, timestamp: float, source_id: int, spell_id: int, target_id: int) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=source_id,
            spell=spell_id,
            target=target_id,
        )

    @classmethod
    def create_setup_event(cls, event_id: int, timestamp: float, source_id: int, spell_id: int) -> 'CombatEvent':
        return CombatEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=source_id,
            spell=spell_id,
        )

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
