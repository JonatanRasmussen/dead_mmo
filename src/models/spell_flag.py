from enum import Flag, auto


class SpellFlag(Flag):
    """ Various Spell boolians """
    NONE = 0
    SELF_CAST = auto()
    TAB_TARGET = auto()
    TARGET_ALL = auto()
    STEP_UP = auto()
    STEP_LEFT = auto()
    STEP_DOWN = auto()
    STEP_RIGHT = auto()
    SET_ABILITY_SLOT_1 = auto()
    SET_ABILITY_SLOT_2 = auto()
    SET_ABILITY_SLOT_3 = auto()
    SET_ABILITY_SLOT_4 = auto()
    TELEPORT = auto()
    TRIGGER_GCD = auto()
    DAMAGE = auto()
    HEAL = auto()
    DENY_IF_CASTING = auto()
    IS_CHANNEL = auto()
    WARP_TO_POSITION = auto()
    TRY_MOVE = auto()
    FORCE_MOVE = auto()
    IS_SETUP = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    AURA_APPLY = auto()
    AURA_CANCEL = auto()