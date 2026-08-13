from dataclasses import dataclass
from typing import Dict, Optional

from src.settings import Consts
from src.world_state._spell_database import SpellDatabase


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


class VfxAndSfxSystem:
    """
    Manages all cosmetic rendering logic, sprites, animations, and sound effects.
    """
    def __init__(self, spell_database: SpellDatabase) -> None:
        # Maps spell_id -> SpellVfxData
        self.spell_data_dct: Dict[int, SpellVfxData] = self._create_initialized_spell_data_dct(spell_database)
        # Maps obj_id -> ObjVfxData
        self.game_obj_vfx_dct: Dict[int, ObjVfxData] = {}

    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> Dict[int, SpellVfxData]:
        spell_data_dct = {}
        for spell in spell_database.get_all_spells():
            spawn_template = None
            if spell.spawned_obj is not None and spell.spawned_obj.game_obj is not None:
                g_obj = spell.spawned_obj.game_obj
                spawn_template = SpellVisualTemplate(
                    color=g_obj.color,
                    sprite_name=g_obj.sprite_name,
                    audio_name=g_obj.audio_name
                )

            spell_data_dct[spell.spell_id] = SpellVfxData(
                audio_name=spell.audio_name,
                animation_name=spell.animation_name,
                animation_scale=spell.animation_scale,
                animate_on_target=spell.animate_on_target,
                spawn_template=spawn_template
            )
        return spell_data_dct

    def create_environment_obj(self, obj_id: int) -> None:
        """Sets up default, invisible rendering for the environment object."""
        self.game_obj_vfx_dct[obj_id] = ObjVfxData(
            color=(255, 255, 255),
            sprite_name="",
            audio_name=""
        )

    def spawn_game_obj(self, obj_id: int, spell_id: int) -> None:
        """Assigns the cosmetic template of the spell to a newly spawned object."""
        spell_data = self.spell_data_dct.get(spell_id)

        if spell_data and spell_data.spawn_template:
            self.game_obj_vfx_dct[obj_id] = ObjVfxData(
                color=spell_data.spawn_template.color,
                sprite_name=spell_data.spawn_template.sprite_name,
                audio_name=spell_data.spawn_template.audio_name
            )
        else:
            # Fallback if spawned without proper visual template
            self.game_obj_vfx_dct[obj_id] = ObjVfxData(
                color=(255, 255, 255),
                sprite_name="",
                audio_name=""
            )

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_vfx_dct.pop(obj_id, None)

    def get_spell_visuals(self, spell_id: int) -> Optional[SpellVfxData]:
        """Returns visual/audio data to play when a spell is cast."""
        return self.spell_data_dct.get(spell_id)

    def get_obj_visuals(self, obj_id: int) -> Optional[ObjVfxData]:
        """Returns the sprite and color payload used to render an object."""
        return self.game_obj_vfx_dct.get(obj_id)