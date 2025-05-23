from typing import NamedTuple, List
from enum import Enum, auto

from src.models.aura import Aura
from src.models.spell import Spell, GameObj, IdGen


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = auto()
    FAILED_NOT_WITHIN_RANGE = auto()
    FAILED_GCD_NOT_READY = auto()
    FAILED_SOURCE_HAS_DESPAWNED = auto()
    FAILED_TARGET_HAS_DESPAWNED = auto()


class UpcomingEvent(NamedTuple):
    event_id: int = IdGen.EMPTY_ID
    base_event: int = IdGen.EMPTY_ID
    timestamp: float = -1.0
    source: int = IdGen.EMPTY_ID
    spell: int = IdGen.EMPTY_ID
    target: int = IdGen.EMPTY_ID
    is_periodic_tick: bool = False

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] (obj_{self.source:04d} uses spell_{self.spell:04d} on obj_{self.target:04d}.)"

    @property
    def is_subevent(self) -> bool:
        return not IdGen.is_empty_id(self.base_event)

    @property
    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.target)

    def update_source_and_target(self, new_source: int, new_target: int) -> 'UpcomingEvent':
        return self._replace(source=new_source, target=new_target)

    def continue_spell_sequence(self, new_event_id: int, new_spell_id: int) -> 'UpcomingEvent':
        return self._replace(event_id=new_event_id, base_event=self.event_id, spell=new_spell_id)

    def also_target(self, new_event_id: int, new_spell_id: int, new_target_id: int) -> 'UpcomingEvent':
        return self._replace(event_id=new_event_id, spell=new_spell_id, target=new_target_id)


class FinalizedEvent(NamedTuple):
    pending_event: UpcomingEvent = UpcomingEvent()
    source: GameObj = GameObj()
    spell: Spell = Spell()
    target: GameObj = GameObj()
    outcome: EventOutcome = EventOutcome.EMPTY

    @property
    def event_id(self) -> int:
        return self.pending_event.event_id
    @property
    def timestamp(self) -> float:
        return self.pending_event.timestamp
    @property
    def is_periodic_tick(self) -> bool:
        return self.pending_event.is_periodic_tick

    @property
    def source_id(self) -> int:
        return self.source.obj_id
    @property
    def spell_id(self) -> int:
        return self.spell.spell_id
    @property
    def target_id(self) -> int:
        return self.target.obj_id

    @property
    def outcome_is_valid(self) -> bool:
        return self.outcome == EventOutcome.SUCCESS

    def update_source(self, new_source: GameObj) -> 'FinalizedEvent':
        return self._replace(source=new_source)


class EventFactory:
    @staticmethod
    def create_finalized_event(origin_event: UpcomingEvent, source: GameObj, spell: Spell, target: GameObj, outcome: EventOutcome) -> FinalizedEvent:
        return FinalizedEvent(
            pending_event=origin_event,
            source=source,
            spell=spell,
            target=target,
            outcome=outcome
        )

    @staticmethod
    def create_setup_event(event_id: int, timestamp: float, spell_id: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=event_id,
            timestamp=timestamp,
            spell=spell_id,
        )

    @staticmethod
    def create_aura_tick_event(event_id: int, timestamp: float, aura: Aura) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=aura.source_id,
            spell=aura.aura_effect_id,
            target=aura.target_id,
            is_periodic_tick=True,
        )

    @staticmethod
    def create_controls_event(event_id: int, timestamp: float, spell_id: int, source_obj: GameObj) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=source_obj.obj_id,
            spell=spell_id,
            target=source_obj.current_target,
        )
