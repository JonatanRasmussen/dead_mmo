from enum import IntFlag, auto

class KeyPresses(IntFlag):
    """ Various bitflags representing a set of keypress game inputs. """
    NONE = 0

    ABILITY_1 = auto()
    ABILITY_2 = auto()
    ABILITY_3 = auto()
    ABILITY_4 = auto()

    SWAP_TARGET = auto()

    START_MOVE_UP = auto()
    STOP_MOVE_UP = auto()
    START_MOVE_LEFT = auto()
    STOP_MOVE_LEFT = auto()
    START_MOVE_DOWN = auto()
    STOP_MOVE_DOWN = auto()
    START_MOVE_RIGHT = auto()
    STOP_MOVE_RIGHT = auto()

