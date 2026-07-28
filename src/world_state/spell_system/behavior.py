from enum import IntFlag, auto

class Behavior(IntFlag):
    """ Various bitflags that define spell behavior. """
    NONE = 0
    STEP_UP = auto()
    STEP_LEFT = auto()
    STEP_DOWN = auto()
    STEP_RIGHT = auto()
    MOVE_TOWARDS_TARGET = auto()
    TELEPORT_TO_TARGET = auto()
    TRIGGER_GCD = auto()
    DAMAGING = auto()
    HEALING = auto()
    AOE = auto()
    DENY_IF_CASTING = auto()
    IS_CHANNEL = auto()
    TRY_MOVE = auto()
    FORCE_MOVE = auto()
    UPDATE_CURRENT_TARGET = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    AURA_APPLY = auto()
    AURA_CANCEL = auto()