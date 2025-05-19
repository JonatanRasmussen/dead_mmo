from typing import Tuple, Optional, NamedTuple
from enum import Flag, auto

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj


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
    HAS_RANGE_LIMIT = auto()
    IGNORE_TARGET = auto()
    DESPAWN = auto()
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


class Spell(NamedTuple):
    """ An action that can be performed by a game object. """
    spell_id: int = IdGen.EMPTY_ID
    alias_id: int = IdGen.EMPTY_ID
    effect_id: int = IdGen.EMPTY_ID

    power: float = 1.0
    variance: float = 0.0

    range_limit: float = 0.0
    #self.cost: float = 0 #not yet implemented
    #self.gcd_mod: float = 0.0 #not yet implemented
    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 1

    flags: SpellFlag = SpellFlag.NONE

    spell_sequence: Optional[Tuple[int, ...]] = None
    spawned_obj: Optional['GameObj'] = None
    obj_controls: Optional[Tuple[Controls, ...]] = None

    @property
    def is_modifying_source(self) -> bool:
        return bool(self.flags & SpellFlag.TRIGGER_GCD)

    @property
    def is_aoe(self) -> bool:
        return bool(self.flags & SpellFlag.TARGET_ALL)

    @property
    def has_aura_apply(self) -> bool:
        return bool(self.flags & SpellFlag.AURA_APPLY)

    @property
    def has_aura_cancel(self) -> bool:
        return bool(self.flags & SpellFlag.AURA_CANCEL)

    @property
    def has_spawned_object(self) -> bool:
        return self.spawned_obj is not None

    @property
    def has_cascading_events(self) -> bool:
        return self.is_aoe or self.has_aura_apply or self.spell_sequence is not None