from dataclasses import dataclass
from enum import Enum

from pygame import display
from src.settings import Consts
from .system_interface import DisplayObj, GameObj, System


class DisplayEffect(str, Enum):
    APPLY_COLOR_RED = "color_red"
    APPLY_COLOR_GREEN = "color_green"
    APPLY_COLOR_BLUE = "color_blue"
    APPLY_ICON_ID = "icon_id"
    TURN_INVISIBLE = "turn_invisible"
    START_PLAY_AUDIO = "play_audio"
    START_PLAY_ANIMATION = "play_animation"


class DisplayValidation(str, Enum):
    pass


@dataclass(slots=True)
class ObjDisplayData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    color_red: int = 255
    color_green: int = 255
    color_blue: int = 255
    color_alpha: float = 1.0
    icon_id: int = Consts.EMPTY_ASSET_ID
    is_visible: bool = True
    audio_id: int = Consts.EMPTY_ASSET_ID
    audio_start: int = Consts.EMPTY_TIMESTAMP
    animation_id: int = Consts.EMPTY_ASSET_ID
    animation_start: int = Consts.EMPTY_TIMESTAMP
    animation_animation_ms_per_frame: int = 100
    animation_scale: float = 0.1

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjDisplayData":
        return cls(obj_id=game_obj.obj_id)


class DisplaySystem(System):

    def __init__(self) -> None:
        self._game_objs: dict[int, GameObj] = {}
        self._data_dct: dict[int, ObjDisplayData] = {}

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            data = self.get_data(obj_id)
            display_obj.is_visible = data.is_visible
            display_obj.color_rgb = (data.color_red, data.color_green, data.color_blue)
            display_obj.sprite_id = data.icon_id
            display_obj.audio_id = data.audio_id
            display_obj.audio_start = data.audio_start
            display_obj.animation_id = data.animation_id
            display_obj.animation_start = data.animation_start
            display_obj.animation_ms_per_frame = data.animation_animation_ms_per_frame
            display_obj.animation_scale = data.animation_scale
        return display_obj

    def get_effect_types(self) -> set[str]:
        return {e.value for e in DisplayEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in DisplayValidation}

    def spawn_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self._game_objs, f"Error: GameObj {game_obj.obj_id} already exist."
        self._game_objs[game_obj.obj_id] = game_obj

    def get_data(self, obj_id: int) -> ObjDisplayData:
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]
        assert obj_id in self._game_objs, f"Error: GameObj {obj_id} does not exist."
        game_obj = self._game_objs[obj_id]
        data = ObjDisplayData.create_from_game_obj(game_obj)
        self._data_dct[obj_id] = data
        return data

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

    # ---- State Lookups ----

    def is_visible(self, obj_id: int) -> bool:
        if obj_id in self._game_objs or obj_id in self._data_dct:
            return self.get_data(obj_id).is_visible
        return ObjDisplayData().is_visible

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> None:
        match effect_type:
            case DisplayEffect.APPLY_COLOR_RED:
                self.get_data(obj_id).color_red = int(effect_value)
            case DisplayEffect.APPLY_COLOR_GREEN:
                self.get_data(obj_id).color_green = int(effect_value)
            case DisplayEffect.APPLY_COLOR_BLUE:
                self.get_data(obj_id).color_blue = int(effect_value)
            case DisplayEffect.APPLY_ICON_ID:
                self.get_data(obj_id).icon_id = int(effect_value)
            case DisplayEffect.TURN_INVISIBLE:
                self.get_data(obj_id).is_visible = False
            case DisplayEffect.START_PLAY_AUDIO:
                data = self.get_data(obj_id)
                data.audio_id = int(effect_value)
                data.audio_start = timestamp
            case DisplayEffect.START_PLAY_ANIMATION:
                data = self.get_data(obj_id)
                data.animation_id = int(effect_value)
                data.animation_start = timestamp