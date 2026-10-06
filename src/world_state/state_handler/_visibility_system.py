from dataclasses import dataclass
from enum import Enum

from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj

class VisibilityEffect(str, Enum):
    APPLY_COLOR_RED = "color_red"
    APPLY_COLOR_GREEN = "color_green"
    APPLY_COLOR_BLUE = "color_blue"
    TURN_INVISIBLE = "turn_invisible"

class VisibilityValidation(str, Enum):
    pass

@dataclass(slots=True)
class ObjVisibilityData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    color_red: int = 255
    color_green: int = 255
    color_blue: int = 255
    color_alpha: float = 1.0
    is_visible: bool = True
    icon_id: int = Consts.EMPTY_ASSET_ID

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjVisibilityData":
        return cls(obj_id=game_obj.obj_id)


class VisibilitySystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjVisibilityData, VisibilityEffect, VisibilityValidation)

    def get_data(self, obj_id: int) -> ObjVisibilityData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            data = self.get_data(obj_id)
            display_obj.is_visible = data.is_visible
            display_obj.color_rgb = (data.color_red, data.color_green, data.color_blue)
        return display_obj

    # ---- State Lookups ----
    def is_visible(self, obj_id: int) -> bool:
        if obj_id in self._game_objs or obj_id in self._data_dct:
            return self.get_data(obj_id).is_visible
        return ObjVisibilityData().is_visible

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        match effect_type:
            case VisibilityEffect.APPLY_COLOR_RED:
                self.get_data(obj_id).color_red = int(effect_value)
                return Consts.EMPTY_SPELL_ID
            case VisibilityEffect.APPLY_COLOR_GREEN:
                self.get_data(obj_id).color_green = int(effect_value)
                return Consts.EMPTY_SPELL_ID
            case VisibilityEffect.APPLY_COLOR_BLUE:
                self.get_data(obj_id).color_blue = int(effect_value)
                return Consts.EMPTY_SPELL_ID
            case VisibilityEffect.TURN_INVISIBLE:
                self.get_data(obj_id).is_visible = False
                return Consts.EMPTY_SPELL_ID
            case _:
                return Consts.EMPTY_SPELL_ID