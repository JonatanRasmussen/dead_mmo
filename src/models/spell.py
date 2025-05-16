from typing import Tuple, Optional, NamedTuple
from enum import Flag, auto

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj


class SpellFlag(Flag):
    """ Flags for how spells should be handled. """
    NONE = 0
    BEGIN_MOVE_UP = auto()
    STOP_MOVE_UP = auto()
    BEGIN_MOVE_LEFT = auto()
    STOP_MOVE_LEFT = auto()
    BEGIN_MOVE_DOWN = auto()
    STOP_MOVE_DOWN = auto()
    BEGIN_MOVE_RIGHT = auto()
    STOP_MOVE_RIGHT = auto()
    STEP_UP = auto()
    STEP_LEFT = auto()
    STEP_DOWN = auto()
    STEP_RIGHT = auto()
    SELF_CAST = auto()
    TAB_TARGET = auto()
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
    SLOT_1_ABILITY = auto()


class Spell(NamedTuple):
    """ An action that can be performed by a game object. """
    spell_id: int = IdGen.EMPTY_ID
    alias_id: int = IdGen.EMPTY_ID
    aura_effect_id: int = IdGen.EMPTY_ID

    power: float = 1.0
    variance: float = 0.0

    #self.cost: float = 0 #not yet implemented
    #self.range_limit: float = 0 #not yet implemented
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
    def has_aura_apply(self) -> bool:
        return bool(self.flags & SpellFlag.AURA_APPLY)

    @property
    def has_aura_cancel(self) -> bool:
        return bool(self.flags & SpellFlag.AURA_CANCEL)

    @property
    def has_spawned_object(self) -> bool:
        return self.spawned_obj is not None

    @property
    def has_spell_sequence(self) -> bool:
        return self.spell_sequence is not None

    @property
    def has_cascading_events(self) -> bool:
        return self.has_aura_apply or self.has_spell_sequence