from enum import Enum, IntFlag, auto
from typing import Tuple, Optional
from dataclasses import dataclass, field
from src.settings import Consts

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
    IS_CHANNEL = auto()

class MovementSpellFlags(IntFlag):
    """ Various bitflags that define spell movement behavior. """
    NONE = 0
    MOVE_UP = auto()
    MOVE_LEFT = auto()
    MOVE_DOWN = auto()
    MOVE_RIGHT = auto()
    STOP_MOVE_UP = auto()
    STOP_MOVE_LEFT = auto()
    STOP_MOVE_DOWN = auto()
    STOP_MOVE_RIGHT = auto()
    MOVE_TOWARDS_TARGET = auto()
    STOP_MOVE_TOWARDS_TARGET = auto()
    TELEPORT_TO_TARGET = auto()
    FORCE_MOVE = auto()
    TRY_MOVE = auto()
    DESPAWN_SELF = auto()
    APPLY_VELOCITY = auto()
    REMOVE_VELOCITY = auto()

class TargetingSpellFlags(IntFlag):
    """Non-combat, non-movement spell flags related to targeting."""
    NONE = 0
    AOE = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    UPDATE_CURRENT_TARGET = auto()

class TargetingSpellMode(Enum):
    """ Defines targeting behavior for spell """
    NONE = 0
    SELF = auto()
    USE_EVENT_TARGET = auto()
    TARGET = auto()
    TARGET_OF_TARGET = auto()
    PARENT = auto()
    TARGET_OF_PARENT = auto()
    DEFAULT_SAME_TEAM = auto()
    DEFAULT_CROSS_TEAM = auto()
    TAB_TO_NEXT = auto()


@dataclass(slots=True)
class SpellData:
    """A flattened, system-agnostic configuration container for spells."""
    spell_id: int
    name: str = ""

    # Extracted Behaviors (Now System-Agnostic)
    casting_behavior: CastingSpellFlags = CastingSpellFlags.NONE
    health_behavior: HealthSpellFlags = HealthSpellFlags.NONE
    movement_behavior: MovementSpellFlags = MovementSpellFlags.NONE
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
    cast_time: int = 0
    spawned_x_offset: float = 0.0
    spawned_y_offset: float = 0.0
    spawned_movespeed: float = 1.0

    # Targeting Data
    targeting: TargetingSpellMode = TargetingSpellMode.NONE

    # VFX/SFX Data
    audio_name: str = ""
    animation_name: str = ""
    animation_scale: float = 1.0
    animate_on_target: bool = True

    # Spawn Cosmetic Data
    spawn_color: Optional[Tuple[int, int, int]] = None
    spawn_sprite_name: str = ""
    spawn_audio_name: str = ""