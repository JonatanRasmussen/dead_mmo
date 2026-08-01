from enum import IntFlag, auto

class Behavior(IntFlag):
    """ Various bitflags that define spell behavior. """
    NONE = 0

    # MOVEMENT
    STEP_UP = auto()
    STEP_LEFT = auto()
    STEP_DOWN = auto()
    STEP_RIGHT = auto()
    MOVE_TOWARDS_TARGET = auto()
    TELEPORT_TO_TARGET = auto()
    FORCE_MOVE = auto()
    TRY_MOVE = auto()

    # COMBATSTATS
    DAMAGING = auto()
    HEALING = auto()

    # STATE UPDATE
    IS_CHANNEL = auto()

    # TARGETING
    AOE = auto()
    UPDATE_CURRENT_TARGET = auto()

    # VALIDATION
    TRIGGER_GCD = auto()
    DENY_IF_CASTING = auto()

    # OBJ SPAWN
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()

    # AURA FLAGS
    AURA_APPLY = auto()
    AURA_CANCEL = auto()