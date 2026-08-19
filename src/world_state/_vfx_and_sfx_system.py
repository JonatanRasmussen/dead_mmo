from dataclasses import dataclass
from typing import Dict, Optional

from src.settings import Consts


@dataclass(slots=True)
class SpellVisualTemplate:
    """Stores the cosmetic data extracted from a Spell's spawned_obj template."""
    color: tuple[int, int, int]
    sprite_name: str
    audio_name: str


@dataclass(slots=True)
class SpellVfxData:
    """Stores visual/audio data for the spell itself."""
    audio_name: str
    animation_name: str
    animation_scale: float
    animate_on_target: bool
    spawn_template: Optional[SpellVisualTemplate] = None

    @property
    def should_play_audio(self) -> bool:
        return bool(self.audio_name)

    @property
    def should_play_animation(self) -> bool:
        return bool(self.animation_name)


@dataclass(slots=True)
class ObjVfxData:
    """ECS-style component storing rendering data for a GameObj."""
    color: tuple[int, int, int]
    sprite_name: str
    audio_name: str

    @classmethod
    def create_environment(cls) -> 'ObjVfxData':
        return cls(
            color=(255, 255, 255),
            sprite_name="",
            audio_name=""
        )

    @classmethod
    def create_from_spell(cls, spell_data: Optional[SpellVfxData]) -> 'ObjVfxData':
        if spell_data and spell_data.spawn_template:
            return cls(
                color=spell_data.spawn_template.color,
                sprite_name=spell_data.spawn_template.sprite_name,
                audio_name=spell_data.spawn_template.audio_name
            )
        return cls(
            color=(255, 255, 255),
            sprite_name="",
            audio_name=""
        )


class VfxAndSfxSystem:
    """
    Manages all cosmetic rendering logic, sprites, animations, and sound effects.
    """
    def __init__(self, spell_data_dct: Dict[int, SpellVfxData]) -> None:
        self.spell_data_dct: Dict[int, SpellVfxData] = spell_data_dct
        self.game_obj_vfx_dct: Dict[int, ObjVfxData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        """Sets up default, invisible rendering for the environment object."""
        self.game_obj_vfx_dct[obj_id] = ObjVfxData.create_environment()

    def spawn_game_obj(self, obj_id: int, spell_id: int) -> None:
        """Assigns the cosmetic template of the spell to a newly spawned object."""
        spell_data = self.spell_data_dct.get(spell_id)
        self.game_obj_vfx_dct[obj_id] = ObjVfxData.create_from_spell(spell_data)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_vfx_dct.pop(obj_id, None)

    def get_spell_visuals(self, spell_id: int) -> SpellVfxData:
        """Returns visual/audio data to play when a spell is cast."""
        return self.spell_data_dct[spell_id]

    def get_obj_visuals(self, obj_id: int) -> ObjVfxData:
        """Returns the sprite and color payload used to render an object."""
        return self.game_obj_vfx_dct[obj_id]