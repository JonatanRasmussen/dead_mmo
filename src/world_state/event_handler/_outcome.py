from enum import Enum, auto

class Outcome(Enum):
    EMPTY = 0
    SUCCESS = auto()
    OUT_OF_RANGE = auto()
    GCD_NOT_READY = auto()
    COOLDOWN_NOT_READY = auto()
    NO_TARGET_WAS_SELECTED = auto()
    OUT_OF_CHANNELING_TICKS = auto()
    SOURCE_IS_DISABLED = auto()
    TARGET_IS_INVALID = auto()
    AURA_NO_LONGER_EXISTS = auto()