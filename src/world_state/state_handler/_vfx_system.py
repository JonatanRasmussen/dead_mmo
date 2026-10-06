from dataclasses import dataclass
from enum import Enum

from src.settings import Consts
from .system_interface import DisplayObj, GameObj, System

class VfxEffect(str, Enum):
    APPLY_ANIMATION_ID = "animation_id"
    START_PLAY_ANIMATION = "play_animation"
    ANIMATION_FRAMES = "animation_frames"
    ANIMATION_MS_PER_FRAME = "animation_speed"
    ANIMATION_LOOPS = "animation_loops"
    ANIMATION_SCALE = "animation_scale"

class VfxValidation(str, Enum):
    pass

@dataclass(slots=True)
class ObjVfxData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    animation_id: int = Consts.EMPTY_ASSET_ID
    animation_start: int = Consts.EMPTY_TIMESTAMP
    animation_ms_per_frame: int = 100
    animation_frames: int = 1
    animation_loops: bool = False
    animation_scale: float = 0.0

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjVfxData":
        return cls(obj_id=game_obj.obj_id)


class VfxSystem(System):

    def __init__(self) -> None:
        self._game_objs: dict[int, GameObj] = {}
        self._data_dct: dict[int, ObjVfxData] = {}

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            data = self.get_data(obj_id)
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
        return {e.value for e in VfxEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in VfxValidation}

    def spawn_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self._game_objs, f"Error: GameObj {game_obj.obj_id} already exist."
        self._game_objs[game_obj.obj_id] = game_obj

    def get_data(self, obj_id: int) -> ObjVfxData:
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]
        assert obj_id in self._game_objs, f"Error: GameObj {obj_id} does not exist."
        game_obj = self._game_objs[obj_id]
        data = ObjVfxData.create_from_game_obj(game_obj)
        self._data_dct[obj_id] = data
        return data

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        match effect_type:
            case VfxEffect.APPLY_ANIMATION_ID:
                self.get_data(obj_id).animation_id = int(effect_value)
                return Consts.EMPTY_SPELL_ID
            case VfxEffect.ANIMATION_FRAMES:
                self.get_data(obj_id).animation_frames = int(effect_value)
                return Consts.EMPTY_SPELL_ID
            case VfxEffect.ANIMATION_MS_PER_FRAME:
                self.get_data(obj_id).animation_ms_per_frame = int(effect_value)
                return Consts.EMPTY_SPELL_ID
            case VfxEffect.ANIMATION_LOOPS:
                self.get_data(obj_id).animation_loops = bool(effect_value)
                return Consts.EMPTY_SPELL_ID
            case VfxEffect.ANIMATION_SCALE:
                self.get_data(obj_id).animation_scale = effect_value
                return Consts.EMPTY_SPELL_ID
            case VfxEffect.START_PLAY_ANIMATION:
                data = self.get_data(obj_id)
                data.animation_start = timestamp if effect_value != 0 else Consts.EMPTY_TIMESTAMP
                return Consts.EMPTY_SPELL_ID
            case _:
                return Consts.EMPTY_SPELL_ID