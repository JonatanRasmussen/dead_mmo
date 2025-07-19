from dataclasses import dataclass, field
import math

from src.settings import Colors, Consts
from .faction import Faction
from .loadout import Loadout
from .status import Status
from .position import Position
from .resources import Resources
from .visuals import Visuals


@dataclass(slots=True)
class GameObj:
    """ Players, NPCs, terrain, projectiles, hitboxes or similar. """
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell: int = Consts.EMPTY_ID

    # Status
    loadout: Loadout = field(default_factory=Loadout)  # Spells and cooldowns
    pos: Position = field(default_factory=Position)  # Coordinates and orientation in space
    res: Resources = field(default_factory=Resources)  # HP, Mana, Ability Charges, etc.
    state: Status = Status.EMPTY  # Alive, Dead, Despawned, Stunned, Casting, etc.
    current_target: int = Consts.EMPTY_ID
    selected_spell: int = Consts.EMPTY_ID

    # Combat stats
    is_attackable: bool = False
    gcd_mod: float = 1.0

    # Cosmetics and Appearance
    color: tuple[int, int, int] = Colors.WHITE
    sprite_name: str = ""
    audio_name: str = ""

    @classmethod
    def create_environment(cls, obj_id: int) -> 'GameObj':
        env_obj = GameObj()
        env_obj.obj_id=obj_id
        env_obj.state=Status.ENVIRONMENT
        env_obj.res.team=Faction.NEUTRAL
        env_obj.current_target=obj_id
        return env_obj

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
        return min(1.0, (current_time - self.loadout.gcd_start) / gcd)
