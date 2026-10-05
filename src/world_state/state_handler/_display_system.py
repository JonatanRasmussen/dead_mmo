from dataclasses import dataclass
from enum import Enum

from pygame import display
from src.settings import Consts
from .system_interface import DisplayObj, GameObj, System

class DisplayEffect(str, Enum):
    APPLY_COLOR_RED = "color_red"
    APPLY_COLOR_GREEN = "color_green"
    APPLY_COLOR_BLUE = "color_blue"
    APPLY_ANIMATION_ID = "animation_id"
    TURN_INVISIBLE = "turn_invisible"
    START_PLAY_AUDIO = "play_audio"
    START_PLAY_ANIMATION = "play_animation"
    ANIMATION_FRAMES = "animation_frames"
    ANIMATION_MS_PER_FRAME = "animation_speed"
    ANIMATION_LOOPS = "animation_loops"
    ANIMATION_SCALE = "animation_scale"

class DisplayValidation(str, Enum):
    pass

@dataclass(slots=True)
class ObjDisplayData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    color_red: int = 255
    color_green: int = 255
    color_blue: int = 255
    color_alpha: float = 1.0
    is_visible: bool = True
    audio_id: int = Consts.EMPTY_ASSET_ID
    audio_start: int = Consts.EMPTY_TIMESTAMP
    animation_id: int = Consts.EMPTY_ASSET_ID
    animation_start: int = Consts.EMPTY_TIMESTAMP
    animation_ms_per_frame: int = 100
    animation_frames: int = 1
    animation_loops: bool = False
    animation_scale: float = 0.0

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
            display_obj.audio_id = float(data.audio_id)
            display_obj.audio_start = data.audio_start
            display_obj.sprite_id = float(data.animation_id)
            display_obj.sprite_index = self._get_sprite_index(current_time, obj_id)
            display_obj.sprite_scale = data.animation_scale
        return display_obj

    def _get_sprite_index(self, current_time: int, obj_id: int) -> int:
        """Calculates current frame and returns (asset_id, frame_index)"""
        data = self.get_data(obj_id)
        elapsed_ms = current_time - data.animation_start
        if (data.animation_id == Consts.EMPTY_ASSET_ID or
            data.animation_start == Consts.EMPTY_TIMESTAMP or
            data.animation_ms_per_frame <= 0 or
            data.animation_frames <= 0 or
            elapsed_ms >= data.animation_frames * data.animation_ms_per_frame * data.animation_loops):
            return 0
        # Calculate current frame index (1-index based, e.g., explosion_1.png)
        frame_index = int(elapsed_ms / data.animation_ms_per_frame)
        current_frame = (frame_index % data.animation_frames) + 1
        return current_frame

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
            case DisplayEffect.APPLY_ANIMATION_ID:
                self.get_data(obj_id).animation_id = int(effect_value)
            case DisplayEffect.ANIMATION_FRAMES:
                self.get_data(obj_id).animation_frames = int(effect_value)
            case DisplayEffect.ANIMATION_MS_PER_FRAME:
                self.get_data(obj_id).animation_ms_per_frame = int(effect_value)
            case DisplayEffect.ANIMATION_LOOPS:
                self.get_data(obj_id).animation_loops = bool(effect_value)
            case DisplayEffect.ANIMATION_SCALE:
                self.get_data(obj_id).animation_scale = effect_value
            case DisplayEffect.TURN_INVISIBLE:
                self.get_data(obj_id).is_visible = False
            case DisplayEffect.START_PLAY_AUDIO:
                data = self.get_data(obj_id)
                data.audio_id = int(effect_value)
                data.audio_start = timestamp
            case DisplayEffect.START_PLAY_ANIMATION:
                data = self.get_data(obj_id)
                data.animation_start = timestamp if effect_value != 0 else Consts.EMPTY_TIMESTAMP