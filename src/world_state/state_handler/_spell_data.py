from enum import Enum, IntFlag, auto
from typing import Tuple, Optional
from dataclasses import dataclass, field
from src.settings import Consts
from .temp_registry import AssetRegistry, InputRegistry

# ==========================================
# Config-Level Spell Flags and Modes
# ==========================================

class CastingSpellFlags(IntFlag):
    """ Various bitflags that define spell casting and cooldown behavior. """
    NONE = 0
    TRIGGER_GCD = auto()
    TRIGGER_COOLDOWN = auto()
    DENY_IF_CASTING = auto()
    START_CHANNEL = auto()
    STOP_CHANNEL = auto()

class HealthSpellFlags(IntFlag):
    """ Various bitflags that define spell health behavior. """
    NONE = 0
    DAMAGING = auto()
    HEALING = auto()

class MovementSpellMode(Enum):
    """ Enumeration of distinct spell movement behaviors. """
    NONE = 0
    # WASD MOVEMENT
    WALK_FORWARD = auto()
    WALK_LEFT = auto()
    WALK_BACKWARD = auto()
    WALK_RIGHT = auto()
    STOP_WALK_FORWARD = auto()
    STOP_WALK_LEFT = auto()
    STOP_WALK_BACKWARD = auto()
    STOP_WALK_RIGHT = auto()

    # WALK
    WALK_SOURCE_TOWARDS_TARGET = auto()
    STOP_WALK_SOURCE_TOWARDS_TARGET = auto()

    TELEPORT_SOURCE_TO_TARGET = auto()
    DESPAWN_SELF = auto()


class TargetingSpellFlags(IntFlag):
    """Non-combat, non-movement spell flags related to targeting."""
    NONE = 0
    AOE_CROSS_TEAM = auto()
    AOE_SAME_TEAM = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    UPDATE_CURRENT_TARGET = auto()
    TARGETSWAP_TO_OTHER_TEAM = auto()
    TARGETSWAP_TO_PARENT = auto()
    TEAMSWAP = auto()

@dataclass(slots=True)
class SpellData:
    """A flattened, system-agnostic configuration container for spells."""
    spell_id: int
    name: str = ""

    # Extracted Behaviors (Now System-Agnostic)
    casting_behavior: CastingSpellFlags = CastingSpellFlags.NONE
    health_behavior: HealthSpellFlags = HealthSpellFlags.NONE
    movement_behavior: MovementSpellMode = MovementSpellMode.NONE
    targeting_behavior: TargetingSpellFlags = TargetingSpellFlags.NONE

    # Casting Data
    timeline: dict[int, list[int]] = field(default_factory=dict)
    base_cooldown: float = 0.0
    hardware_bindings: dict[str, int] = field(default_factory=dict)
    gcd_mod: float = 1.0

    # Health Data
    power: float = 1.0
    hp: float = 0.0

    # Movement Data
    range_limit: float = 0.0
    movement_force: float = 1.0
    spawned_x_offset: float = 0.0
    spawned_y_offset: float = 0.0
    spawned_movespeed: float = 1.0

    # VFX/SFX Data
    audio_name: str = ""
    animation_name: str = ""
    animation_scale: float = 1.0
    animate_on_target: bool = True

    # Spawn Cosmetic Data
    spawn_color: Optional[Tuple[int, int, int]] = None
    spawn_sprite_name: str = ""
    spawn_audio_name: str = ""

    def __post_init__(self):
        # Dynamically inject assets so the rest of the game doesn't break
        if not self.audio_name:
            self.audio_name = AssetRegistry.get_audio(self.spell_id)
        if not self.spawn_sprite_name:
            self.spawn_sprite_name = AssetRegistry.get_sprite(self.spell_id)

        # Legacy Support: Inject the hardware bindings into spawn_player (Spell 42)
        # so your StateHandler can still find them if it relies on this field.
        if self.spell_id == 42 and not self.hardware_bindings:
            self.hardware_bindings = InputRegistry.BINDINGS