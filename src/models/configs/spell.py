from typing import Iterable, Optional
from dataclasses import dataclass

from src.config import Consts
from src.models.components import Controls, ObjTemplate
from .behavior import Behavior
from .targeting import Targeting


@dataclass(slots=True)
class Spell:
    """ An action that can be performed by a game object. """
    spell_id: int = Consts.EMPTY_ID
    effect_id: int = Consts.EMPTY_ID
    spell_sequence: Optional[tuple[int, ...]] = None

    power: float = 1.0
    variance: float = 0.0

    range_limit: float = 0.0
    #self.cost: float = 0 #not yet implemented
    #self.gcd_mod: float = 0.0 #not yet implemented
    cast_time: int = 0
    duration: int = 0
    ticks: int = 1
    #max_stacks: int = 1 #not yet implemented

    flags: Behavior = Behavior.NONE
    targeting: Targeting = Targeting.NONE

    spawned_obj: Optional[ObjTemplate] = None

    # Audio properties
    audio_name: str = ""
    spell_type: str = ""

    # Animation properties
    animation_name: str = ""
    animation_scale: float = 1.0

    # Effect placement
    animate_on_target: bool = True  # If False, animate on source

    @property
    def copy_obj_controls(self) -> Iterable[Controls]:
        if self.spawned_obj is not None:
            if self.spawned_obj.obj_controls is not None:
                for controls in self.spawned_obj.obj_controls:
                    yield controls.create_copy()

    @property
    def should_play_audio(self) -> bool:
        return bool(self.audio_name)

    @property
    def should_play_animation(self) -> bool:
        return bool(self.animation_name)

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
    def is_target_of_target(self) -> bool:
        return Behavior.TARGET_OF_TARGET in self.flags

    @property
    def is_area_of_effect(self) -> bool:
        return Behavior.AOE in self.flags

    @property
    def has_cascading_events(self) -> bool:
        return (
            self.is_area_of_effect or
            self.has_aura_apply or
            self.spawned_obj is not None or
            self.spell_sequence is not None
        )