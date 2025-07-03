from dataclasses import dataclass, field, replace
import math

from src.config import Colors, Consts
from .hostility import Hostility
from .loadout import Loadout
from .modifiers import Modifiers
from .obj_status import ObjStatus
from .position import Position
from .resources import Resources
from .views import Views
from .waitouts import Waitouts


@dataclass(slots=True)
class GameObj:
    """ Players, NPCs, terrain, projectiles, hitboxes or similar. """
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell: int = Consts.EMPTY_ID

    # Status
    cds: Waitouts = field(default_factory=Waitouts)  # Cooldown timers for abilities and casts
    loadout: Loadout = field(default_factory=Loadout)  # The SpellIDs that are 'equipped' for each Ability slot
    mods: Modifiers = field(default_factory=Modifiers)  # Attack Powers, Damage Resistances, Move Speed etc.
    pos: Position = field(default_factory=Position)  # Coordinates and orientation in space
    res: Resources = field(default_factory=Resources)  # HP, Mana, Ability Charges, etc.
    status: ObjStatus = ObjStatus.EMPTY  # Alive, Dead, Despawned, Stunned, Casting, etc.
    team: Hostility = Hostility.EMPTY  # Helps decide if GameObjs should target each other
    views: Views = field(default_factory=Views)  # Cosmetics such as audio, sprites, animations etc.
    current_target: int = Consts.EMPTY_ID
    selected_spell: int = Consts.EMPTY_ID

    # Combat stats
    is_attackable: bool = False
    gcd: float = 1.0

    # Cosmetics and Appearance
    color: tuple[int, int, int] = Colors.WHITE

    def create_copy(self) -> 'GameObj':
        return replace(
            self,
            cds=replace(self.cds),
            loadout=replace(self.loadout),
            mods=replace(self.mods),
            pos=replace(self.pos),
            res=replace(self.res),
            views=replace(self.views),
        )

    @classmethod
    def create_environment(cls, obj_id: int) -> 'GameObj':
        return GameObj(
            obj_id=obj_id,
            status=ObjStatus.ENVIRONMENT,
            team=Hostility.NEUTRAL,
            current_target=obj_id,
        )

    @property
    def should_play_audio(self) -> bool:
        return self.views.audio_name is not None and self.views.audio_name != ""

    @property
    def should_render_sprite(self) -> bool:
        return self.views.sprite_name is not None and self.views.sprite_name != "" and self.is_visible

    @property
    def size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.res.hp))

    @property
    def spell_modifier(self) -> float:
        return 1.0

    @property
    def is_environment(self) -> bool:
        return self.status in {ObjStatus.ENVIRONMENT}

    @property
    def is_visible(self) -> bool:
        return not self.status in {ObjStatus.ENVIRONMENT, ObjStatus.DESPAWNED}

    @property
    def is_despawned(self) -> bool:
        return self.status == ObjStatus.DESPAWNED

    def get_gcd_progress(self, current_time: float) -> float:
        return min(1.0, (current_time - self.cds.gcd_start) / self.gcd)
