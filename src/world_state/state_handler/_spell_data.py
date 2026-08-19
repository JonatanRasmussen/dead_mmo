from typing import Mapping, Union, Tuple, Optional
from dataclasses import dataclass, field
from src.settings import Consts

# Import the refactored systems and components
from ._casting_system import SpellCastingData, CastingBehavior, Controls
from ._health_system import SpellHealthData, HealthBehavior
from ._movement_system import SpellMovementData, MovementBehavior
from ._targeting_system import SpellTargetingData, TargetingBehavior, Targeting
from ._vfx_and_sfx_system import SpellVfxData, SpellVisualTemplate


@dataclass(slots=True)
class SpellData:
    """A flattened, system-agnostic configuration container for spells."""
    spell_id: int

    # Extracted Behaviors
    casting_behavior: CastingBehavior = CastingBehavior.NONE
    health_behavior: HealthBehavior = HealthBehavior.NONE
    movement_behavior: MovementBehavior = MovementBehavior.NONE
    targeting_behavior: TargetingBehavior = TargetingBehavior.NONE

    # Casting Data
    spell_sequence: tuple[int, ...] = ()
    timeline: Mapping[int, Union[int, tuple[int, ...]]] = field(default_factory=dict)
    effect_id: int = Consts.EMPTY_ID
    duration: int = 0
    ticks: int = 1
    base_cooldown: float = 0.0
    spell_bindings: list[int] = field(default_factory=list)
    controls: tuple[Controls, ...] = ()
    gcd_mod: float = 1.0

    # Health Data
    power: float = 1.0
    hp: float = 0.0

    # Movement Data
    range_limit: float = 0.0
    cast_time: int = 0
    spawned_x_offset: float = 0.0
    spawned_y_offset: float = 0.0
    spawned_movespeed: float = 1.0

    # Targeting Data
    targeting: Targeting = Targeting.NONE

    # VFX/SFX Data
    audio_name: str = ""
    animation_name: str = ""
    animation_scale: float = 1.0
    animate_on_target: bool = True

    # Spawn Cosmetic Data
    spawn_color: Optional[Tuple[int, int, int]] = None
    spawn_sprite_name: str = ""
    spawn_audio_name: str = ""

    # --- System Data Generators ---

    def to_casting_data(self) -> SpellCastingData:
        return SpellCastingData(
            flags=self.casting_behavior,
            spell_sequence=self.spell_sequence,
            timeline=self.timeline,
            effect_id=self.effect_id,
            duration=self.duration,
            ticks=self.ticks,
            base_cooldown=self.base_cooldown,
            spell_bindings=self.spell_bindings,
            controls=self.controls,
            gcd_mod=self.gcd_mod,
        )

    def to_health_data(self) -> SpellHealthData:
        return SpellHealthData(
            power=self.power,
            flags=self.health_behavior,
            hp=self.hp,
        )

    def to_movement_data(self) -> SpellMovementData:
        return SpellMovementData(
            power=self.power,
            range_limit=self.range_limit,
            cast_time=self.cast_time,
            flags=self.movement_behavior,
            spawned_x_offset=self.spawned_x_offset,
            spawned_y_offset=self.spawned_y_offset,
            spawned_movespeed=self.spawned_movespeed,
        )

    def to_targeting_data(self) -> SpellTargetingData:
        is_enemy = bool(self.targeting_behavior & TargetingBehavior.SPAWN_BOSS)
        is_boss_or_player = bool(
            self.targeting_behavior & TargetingBehavior.SPAWN_BOSS or
            self.targeting_behavior & TargetingBehavior.SPAWN_PLAYER
        )
        return SpellTargetingData(
            spell_id=self.spell_id,
            targeting=self.targeting,
            is_enemy=is_enemy,
            is_boss_or_player=is_boss_or_player,
            flags=self.targeting_behavior,
        )

    def to_vfx_data(self) -> SpellVfxData:
        spawn_template = None
        if self.spawn_color is not None:
            spawn_template = SpellVisualTemplate(
                color=self.spawn_color,
                sprite_name=self.spawn_sprite_name,
                audio_name=self.spawn_audio_name
            )

        return SpellVfxData(
            audio_name=self.audio_name,
            animation_name=self.animation_name,
            animation_scale=self.animation_scale,
            animate_on_target=self.animate_on_target,
            spawn_template=spawn_template
        )