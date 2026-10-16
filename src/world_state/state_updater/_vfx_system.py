from dataclasses import dataclass
from enum import Enum

from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj

class VfxEffect(str, Enum):
    DRAW_AS_SQUARE = "draw_as_square"
    APPLY_SPRITE_ID = "sprite_id"
    SPRITE_FRAMES = "sprite_frames"
    ANIMATION_MS_PER_FRAME = "animation_speed"
    ANIMATION_LOOPS = "animation_loops"
    ANIMATION_SCALE = "animation_scale"
    START_PLAY_ANIMATION = "play_animation"

class VfxValidation(str, Enum):
    pass

@dataclass(slots=True)
class ObjVfxData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    draw_as_square: bool = False
    sprite_id: int = Consts.EMPTY_ASSET_ID
    sprite_frames: int = 1
    animation_ms_per_frame: int = 100
    animation_loops: int = 0  # Number of loops to run, NOT boolean
    animation_scale: float = 0.0
    animation_start: int = Consts.EMPTY_TIMESTAMP

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjVfxData":
        return cls(obj_id=game_obj.obj_id)


class VfxSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjVfxData, VfxEffect, VfxValidation)

    def get_data(self, obj_id: int) -> ObjVfxData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            data = self.get_data(obj_id)
            display_obj.draw_as_square = data.draw_as_square
            display_obj.sprite_id = float(data.sprite_id)
            display_obj.sprite_index = self._get_sprite_index(current_time, obj_id)
            display_obj.sprite_scale = data.animation_scale
        return display_obj

    def _get_sprite_index(self, current_time: int, obj_id: int) -> int:
        """Calculates current frame and returns (asset_id, frame_index)"""
        data = self.get_data(obj_id)
        if data.sprite_id == Consts.EMPTY_ASSET_ID:
            return 0
        if data.sprite_frames == 1:  # If it's a static sprite (1 frame), just return frame 1
            return 1
        elapsed_ms = current_time - data.animation_start
        if (data.animation_start == Consts.EMPTY_TIMESTAMP or
            data.animation_ms_per_frame <= 0 or
            data.sprite_frames <= 0 or
            elapsed_ms >= data.sprite_frames * data.animation_ms_per_frame * data.animation_loops):
            return 0
        # Calculate current frame index (1-index based, e.g., explosion_1.png)
        frame_index = int(elapsed_ms / data.animation_ms_per_frame)
        current_frame = (frame_index % data.sprite_frames) + 1
        return current_frame

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case VfxEffect.DRAW_AS_SQUARE:
                self.get_data(obj_id).draw_as_square = bool(effect_value)
            case VfxEffect.APPLY_SPRITE_ID:
                self.get_data(obj_id).sprite_id = effect_value
            case VfxEffect.SPRITE_FRAMES:
                self.get_data(obj_id).sprite_frames = effect_value
            case VfxEffect.ANIMATION_MS_PER_FRAME:
                self.get_data(obj_id).animation_ms_per_frame = effect_value
            case VfxEffect.ANIMATION_LOOPS:
                self.get_data(obj_id).animation_loops = effect_value
            case VfxEffect.ANIMATION_SCALE:
                self.get_data(obj_id).animation_scale = effect_value / 100.0
            case VfxEffect.START_PLAY_ANIMATION:
                data = self.get_data(obj_id)
                data.animation_start = timestamp if effect_value != 0 else Consts.EMPTY_TIMESTAMP
        return triggered_spell_id