from typing import List, Tuple, Iterable, Optional, NamedTuple, ValuesView
from enum import Enum, Flag, auto
from src.config import Consts
from .behavior import Behavior
from .controls import Controls
from .game_obj import GameObj
from .targeting import Targeting


class Spell(NamedTuple):
    """ An action that can be performed by a game object. """
    spell_id: int = Consts.EMPTY_ID
    alias_id: int = Consts.EMPTY_ID

    power: float = 1.0
    variance: float = 0.0

    range_limit: float = 0.0
    #self.cost: float = 0 #not yet implemented
    #self.gcd_mod: float = 0.0 #not yet implemented
    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 1

    flags: Behavior = Behavior.NONE
    targeting: Targeting = Targeting.NONE

    external_spell: int = Consts.EMPTY_ID
    spell_sequence: Optional[Tuple[int, ...]] = None
    spawned_obj: Optional['GameObj'] = None
    obj_controls: Optional[Tuple[Controls, ...]] = None

    # Audio properties
    audio_name: str = ""
    spell_type: str = ""

    # Animation properties
    animation_name: str = ""
    animation_scale: float = 1.0

    # Effect placement
    animate_on_target: bool = True  # If False, animate on source

    @property
    def should_play_audio(self) -> bool:
        return self.audio_name is not None and self.audio_name != ""
    @property
    def should_play_animation(self) -> bool:
        return self.animation_name is not None and self.animation_name != ""

    @property
    def is_modifying_source(self) -> bool:
        return True  # While I'm still frequently adding new flags, just return True
        # return bool(self.flags & SpellFlag.TRIGGER_GCD)

    @property
    def has_range_limit(self) -> bool:
        return self.range_limit > 0.0

    @property
    def has_aura_apply(self) -> bool:
        return Behavior.AURA_APPLY in self.flags

    @property
    def has_aura_cancel(self) -> bool:
        return Behavior.AURA_CANCEL in self.flags

    @property
    def has_cascading_events(self) -> bool:
        return (
            self.is_area_of_effect or
            self.has_aura_apply or
            self.spawned_obj is not None or
            self.spell_sequence is not None
        )

    #Targeting

    @property
    def is_target_of_target(self) -> bool:
        return Behavior.TARGET_OF_TARGET in self.flags

    @property
    def is_area_of_effect(self) -> bool:
        return Behavior.AOE in self.flags
