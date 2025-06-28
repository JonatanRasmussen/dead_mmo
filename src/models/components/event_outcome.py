from typing import Tuple, NamedTuple, Optional
from enum import Enum, auto

from .behavior import Behavior
from .game_obj import GameObj
from .spell import Spell


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = auto()
    OUT_OF_RANGE = auto()
    GCD_NOT_READY = auto()
    NO_TARGET_WAS_SELECTED = auto()
    SOURCE_IS_DISABLED = auto()
    TARGET_IS_INVALID = auto()
    AURA_NO_LONGER_EXISTS = auto()

    @property
    def is_success(self) -> bool:
        return self in {EventOutcome.SUCCESS}

    @staticmethod
    def decide_outcome(timestamp: float, source_obj: GameObj, spell: Spell, target_obj: GameObj, skip_source_validation: bool) -> 'EventOutcome':
        # Validate source
        if not skip_source_validation:
            if not source_obj.status.is_valid_source:
                return EventOutcome.SOURCE_IS_DISABLED
            if not EventOutcome._gcd_is_available(timestamp, source_obj, spell):
                return EventOutcome.GCD_NOT_READY
        # Validate target
        if not target_obj.status.is_valid_target and not source_obj.obj_id == target_obj.obj_id:
            return EventOutcome.TARGET_IS_INVALID
        # Validate source relative to target
        if not EventOutcome._is_within_range(source_obj, spell, target_obj):
            return EventOutcome.OUT_OF_RANGE
        # More outcome conditions to be added here.
        return EventOutcome.SUCCESS

    @staticmethod
    def _is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.has_range_limit:
            return True
        return (source_obj.x - target_obj.x) ** 2 + (source_obj.y - target_obj.y) ** 2 <= spell.range_limit ** 2

    @staticmethod
    def _gcd_is_available(timestamp: float, source_obj: GameObj, spell: Spell) -> bool:
        if not spell.flags & Behavior.TRIGGER_GCD:
            return True
        return source_obj.get_gcd_progress(timestamp) >= 1.0