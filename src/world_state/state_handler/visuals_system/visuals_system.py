from dataclasses import dataclass
from typing import Dict, Optional
from enum import IntFlag, auto


class VisualsBehavior(IntFlag):
    NONE = 0
    CHANGE_COLOR_RGB_OF_SOURCE = auto()
    CHANGE_SPRITE_OF_SOURCE = auto()

@dataclass(slots=True)
class SpellVisualsData:
    """Stores visual/audio data for the spell itself."""
    flags: VisualsBehavior
    audio_name: str
    animation_name: str
    animation_scale: float
    animate_on_source: bool
    animate_on_target: bool
    rgb_color_red: int
    rgb_color_green: int
    rgb_color_blue: int
    obj_sprite_name: str

    @property
    def should_play_audio(self) -> bool:
        return bool(self.audio_name)

    @property
    def should_play_animation(self) -> bool:
        return bool(self.animation_name)


@dataclass(slots=True)
class ObjVisualsData:
    """ECS-style component storing rendering data for a GameObj."""

    color_red: int
    color_green: int
    color_blue: int
    sprite_name: str

    @classmethod
    def create_environment(cls) -> "ObjVisualsData":
        return cls(
            color_red=255,
            color_green=255,
            color_blue=255,
            sprite_name="",
        )

    @classmethod
    def create_from_spell(cls, spell_data: SpellVisualsData) -> "ObjVisualsData":
        return cls(
            color_red=spell_data.rgb_color_red,
            color_green=spell_data.rgb_color_green,
            color_blue=spell_data.rgb_color_blue,
            sprite_name=spell_data.obj_sprite_name,
        )


class VisualsSystem:
    """
    Manages all cosmetic rendering logic, sprites, animations, and sound effects.
    """

    def __init__(self, spell_data_dct: Dict[int, SpellVisualsData]) -> None:
        self.spell_data_dct: Dict[int, SpellVisualsData] = spell_data_dct
        self.game_obj_data_dct: Dict[int, ObjVisualsData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        """Sets up default, invisible rendering for the environment object."""
        self.game_obj_data_dct[obj_id] = ObjVisualsData.create_environment()

    def spawn_game_obj(self, obj_id: int, spell_id: int) -> None:
        """Assigns the cosmetic template of the spell to a newly spawned object."""
        spell_data = self.spell_data_dct[spell_id]
        self.game_obj_data_dct[obj_id] = ObjVisualsData.create_from_spell(spell_data)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    def apply_visuals_event(self, source_id: int, spell_id: int) -> None:
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_data_dct.get(source_id)

        # Apply Target Effects
        if source_data:
            if flags & VisualsBehavior.CHANGE_COLOR_RGB_OF_SOURCE:
                source_data.color_red = spell_data.rgb_color_red
                source_data.color_green = spell_data.rgb_color_green
                source_data.color_blue = spell_data.rgb_color_blue
            if flags & VisualsBehavior.CHANGE_SPRITE_OF_SOURCE:
                source_data.sprite_name = spell_data.obj_sprite_name


    def get_spell_visuals(self, spell_id: int) -> SpellVisualsData:
        """Returns visual/audio data to play when a spell is cast."""
        return self.spell_data_dct[spell_id]

    def get_obj_visuals(self, obj_id: int) -> ObjVisualsData:
        """Returns the sprite and color payload used to render an object."""
        return self.game_obj_data_dct[obj_id]
