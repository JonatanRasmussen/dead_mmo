from typing import Tuple, Optional, NamedTuple
from enum import Flag, auto

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell_flag import SpellFlag

class Spell(NamedTuple):
    """ An action that can be performed by a game object. """
    spell_id: int = IdGen.EMPTY_ID
    alias_id: int = IdGen.EMPTY_ID
    effect_id: int = IdGen.EMPTY_ID

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