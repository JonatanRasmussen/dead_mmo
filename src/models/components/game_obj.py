from dataclasses import dataclass, field
import math

from src.config import Colors, Consts
from src.models.utils.copy_utils import CopyTools
from .faction import Faction
from .loadout import Loadout
from .base_stats import BaseStats
from .status import Status
from .position import Position
from .resources import Resources
from .visuals import Visuals
from .waitouts import Waitouts


@dataclass(slots=True)
class GameObj:
    """ Players, NPCs, terrain, projectiles, hitboxes or similar. """
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell: int = Consts.EMPTY_ID

    # Status
    cds: Waitouts = field(default_factory=Waitouts)  # Cooldown timers for abilities and casts
    loadout: Loadout = field(default_factory=Loadout)  # Spells and cooldowns
    stats: BaseStats = field(default_factory=BaseStats)  # Attack Powers, Damage Resistances, Move Speed etc.
    pos: Position = field(default_factory=Position)  # Coordinates and orientation in space
    res: Resources = field(default_factory=Resources)  # HP, Mana, Ability Charges, etc.
    state: Status = Status.EMPTY  # Alive, Dead, Despawned, Stunned, Casting, etc.
    team: Faction = Faction.EMPTY  # Helps decide if GameObjs should target each other
    current_target: int = Consts.EMPTY_ID
    selected_spell: int = Consts.EMPTY_ID

    # Combat stats
    is_attackable: bool = False
    gcd_mod: float = 1.0

    # Cosmetics and Appearance
    color: tuple[int, int, int] = Colors.WHITE
    sprite_name: str = ""
    audio_name: str = ""


    def create_copy(self) -> 'GameObj':
        return CopyTools.full_copy(self)

    @classmethod
    def create_environment(cls, obj_id: int) -> 'GameObj':
        return GameObj(
            obj_id=obj_id,
            state=Status.ENVIRONMENT,
            team=Faction.NEUTRAL,
            current_target=obj_id,
        )

    @property
    def should_play_audio(self) -> bool:
        return self.audio_name is not None and self.audio_name != ""

    @property
    def should_render_sprite(self) -> bool:
        return self.sprite_name is not None and self.sprite_name != "" and self.is_visible

    @property
    def size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.res.hp))

    @property
    def spell_modifier(self) -> float:
        return 1.0

    @property
    def is_environment(self) -> bool:
        return self.state in {Status.ENVIRONMENT}

    @property
    def is_visible(self) -> bool:
        return not self.state in {Status.ENVIRONMENT, Status.DESPAWNED}

    @property
    def is_despawned(self) -> bool:
        return self.state == Status.DESPAWNED

    def get_gcd_progress(self, current_time: int) -> float:
        gcd = Consts.BASE_GCD * self.gcd_mod
        return min(1.0, (current_time - self.cds.gcd_start) / gcd)
