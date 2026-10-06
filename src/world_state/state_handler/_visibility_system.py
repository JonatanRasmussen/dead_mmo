from dataclasses import dataclass
from enum import Enum

from src.settings import Consts
from .system_interface import DisplayObj, GameObj, System

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


class VisibilitySystem(System):

    def __init__(self) -> None:
        self._game_objs: dict[int, GameObj] = {}
        self._data_dct: dict[int, ObjVisibilityData] = {}

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            data = self.get_data(obj_id)
            display_obj.is_visible = data.is_visible
            display_obj.color_rgb = (data.color_red, data.color_green, data.color_blue)
        return display_obj

    def get_effect_types(self) -> set[str]:
        return {e.value for e in VisibilityEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in VisibilityValidation}

    def spawn_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self._game_objs, f"Error: GameObj {game_obj.obj_id} already exist."
        self._game_objs[game_obj.obj_id] = game_obj

    def get_data(self, obj_id: int) -> ObjVisibilityData:
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]
        assert obj_id in self._game_objs, f"Error: GameObj {obj_id} does not exist."
        game_obj = self._game_objs[obj_id]
        data = ObjVisibilityData.create_from_game_obj(game_obj)
        self._data_dct[obj_id] = data
        return data

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

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