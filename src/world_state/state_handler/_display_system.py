import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from src.settings import Consts

@dataclass(slots=True)
class ObjDisplayData:
    spawn_timestamp: int = 0
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell_id: int = Consts.EMPTY_ID
    color_red: int = 255
    color_green: int = 255
    color_blue: int = 255
    color_alpha: float = 1.0
    icon_id: int = Consts.EMPTY_ID
    is_visible: bool = True
    audio_build_id: int = Consts.EMPTY_ID
    audio_cast_id: int = Consts.EMPTY_ID
    audio_hit_id: int = Consts.EMPTY_ID
    animation_build_id: int = Consts.EMPTY_ID
    animation_cast_id: int = Consts.EMPTY_ID
    animation_hit_id: int = Consts.EMPTY_ID

    @classmethod
    def create_new_obj(cls, timestamp: int, parent_id: int, new_obj_id: int, spell_id: int) -> "ObjDisplayData":
        return cls(
            spawn_timestamp=timestamp,
            obj_id=new_obj_id,
            parent_id=parent_id,
            spawned_from_spell_id=spell_id,
        )

class DisplayEffect(str, Enum):
    APPLY_COLOR_RED = "color_red"
    APPLY_COLOR_GREEN = "color_green"
    APPLY_COLOR_BLUE = "color_blue"
    APPLY_ICON_ID = "icon_id"
    TURN_INVISIBLE = "turn_invisible"
    APPLY_AUDIO_BUILD_ID = "audio_build_id"
    APPLY_AUDIO_CAST_ID = "audio_cast_id"
    APPLY_AUDIO_HIT_ID = "audio_hit_id"
    APPLY_ANIMATION_BUILD_ID = "animation_build_id"
    APPLY_ANIMATION_CAST_ID = "animation_cast_id"
    APPLY_ANIMATION_HIT_ID = "animation_hit_id"

class DisplayInvalidOutcomes(str, Enum):
    pass

class DisplayValidation(str, Enum):
    pass

class DisplaySystem:

    def __init__(self) -> None:
        self._data_dct: Dict[int, ObjDisplayData] = {}

    def spawn_game_obj(self, timestamp: int, parent_id: int, new_obj_id: int, spell_id: int, target_id: int = Consts.EMPTY_ID) -> None:
        game_obj = ObjDisplayData.create_new_obj(timestamp, parent_id, new_obj_id, spell_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjDisplayData(obj_id=obj_id, is_visible=False)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjDisplayData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjDisplayData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

    # ---- State Lookups ----

    def is_visible(self, obj_id: int) -> bool:
        return self._data_dct.get(obj_id, ObjDisplayData()).is_visible

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> str:
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, target_id: int) -> None:
        if effect_type == DisplayEffect.APPLY_COLOR_RED:
            self.get_data(source_id).color_red = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_COLOR_GREEN:
            self.get_data(source_id).color_green = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_COLOR_BLUE:
            self.get_data(source_id).color_blue = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_ICON_ID:
            self.get_data(source_id).icon_id = int(effect_value)
        elif effect_type == DisplayEffect.TURN_INVISIBLE:
            self.get_data(source_id).is_visible = False
        elif effect_type == DisplayEffect.APPLY_AUDIO_BUILD_ID:
            self.get_data(source_id).audio_build_id = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_AUDIO_CAST_ID:
            self.get_data(source_id).audio_cast_id = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_AUDIO_HIT_ID:
            self.get_data(source_id).audio_hit_id = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_ANIMATION_BUILD_ID:
            self.get_data(source_id).animation_build_id = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_ANIMATION_CAST_ID:
            self.get_data(source_id).animation_cast_id = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_ANIMATION_HIT_ID:
            self.get_data(source_id).animation_hit_id = int(effect_value)