from typing import NamedTuple
from enum import Enum, auto

from src.models.aura import Aura
from src.models.spell import SpellFlag, Spell, GameObjStatus, GameObj, IdGen


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = auto()
    OUT_OF_RANGE = auto()
    GCD_NOT_READY = auto()
    NO_TARGET_WAS_SELECTED = auto()
    SOURCE_IS_DISABLED = auto()
    TARGET_IS_INVALID = auto()

    @staticmethod
    def decide_outcome(timestamp: float, source_obj: GameObj, spell: Spell, target_obj: GameObj) -> 'EventOutcome':
        if not target_obj.status.is_valid_target and not source_obj.obj_id == target_obj.obj_id:
            return EventOutcome.TARGET_IS_INVALID
        if not target_obj.status.is_valid_source:
            return EventOutcome.SOURCE_IS_DISABLED
        if not EventOutcome._is_within_range(source_obj, spell, target_obj):
            return EventOutcome.OUT_OF_RANGE
        if not EventOutcome._gcd_is_available(timestamp, source_obj, spell):
            return EventOutcome.GCD_NOT_READY
        return EventOutcome.SUCCESS

    @staticmethod
    def _is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.flags & SpellFlag.HAS_RANGE_LIMIT:
            return True
        return (source_obj.x - target_obj.x) ** 2 + (source_obj.y - target_obj.y) ** 2 <= spell.range_limit ** 2

    @staticmethod
    def _gcd_is_available(timestamp: float, source_obj: GameObj, spell: Spell) -> bool:
        if not spell.flags & SpellFlag.TRIGGER_GCD:
            return True
        return source_obj.get_gcd_progress(timestamp) >= 1.0

class UpcomingEvent(NamedTuple):
    event_id: int = IdGen.EMPTY_ID
    base_event: int = IdGen.EMPTY_ID
    timestamp: float = -1.0
    source: int = IdGen.EMPTY_ID
    spell: int = IdGen.EMPTY_ID
    target: int = IdGen.EMPTY_ID
    is_periodic_tick: bool = False

    @classmethod
    def create_from_aura_tick(cls, event_id: int, timestamp: float, aura: Aura) -> 'UpcomingEvent':
        return UpcomingEvent(
            event_id=event_id,
            timestamp=timestamp,
            source=aura.source_id,
            spell=aura.spell_id,
            target=aura.target_id,
            is_periodic_tick=True,
        )

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] (obj_{self.source:04d} uses spell_{self.spell:04d} on obj_{self.target:04d}.)"

    @property
    def is_subevent(self) -> bool:
        return IdGen.is_valid_id(self.base_event)

    @property
    def has_target(self) -> bool:
        return IdGen.is_valid_id(self.target)

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
    def is_aura_creation(self) -> bool:
        return self.spell.has_aura_apply and not self.pending_event.is_periodic_tick
    @property
    def is_aura_deletion(self) -> bool:
        return self.spell.has_aura_cancel and not self.pending_event.is_periodic_tick
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
