from enum import Enum, auto

from src.models.components import GameObj
from src.models.data import Behavior, Spell


class Outcome(Enum):
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
        return self in {Outcome.SUCCESS}

    @staticmethod
    def decide_outcome(timestamp: int, source_obj: GameObj, spell: Spell, target_obj: GameObj, skip_source_validation: bool) -> 'Outcome':
        # Validate source
        if not skip_source_validation:
            if not source_obj.state.is_valid_source:
                return Outcome.SOURCE_IS_DISABLED
            if not Outcome._gcd_is_available(timestamp, source_obj, spell):
                return Outcome.GCD_NOT_READY
        # Validate target
        if not target_obj.state.is_valid_target and not source_obj.obj_id == target_obj.obj_id:
            return Outcome.TARGET_IS_INVALID
        # Validate source relative to target
        if not Outcome._is_within_range(source_obj, spell, target_obj):
            return Outcome.OUT_OF_RANGE
        # More outcome conditions to be added here.
        return Outcome.SUCCESS

    @staticmethod
    def _is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.has_range_limit:
            return True
        return source_obj.pos.has_target_within_range(target_obj.pos, spell.range_limit)

    @staticmethod
    def _gcd_is_available(timestamp: int, source_obj: GameObj, spell: Spell) -> bool:
        if not spell.flags & Behavior.TRIGGER_GCD:
            return True
        return source_obj.get_gcd_progress(timestamp) >= 1.0