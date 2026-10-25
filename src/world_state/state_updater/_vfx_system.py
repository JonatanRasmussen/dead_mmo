from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .base_system import BaseSystem, GameObj


class VfxEffect(str, Enum):
    IS_VISIBLE = "is_visible"
    COLOR_RED = "color_red"
    COLOR_GREEN = "color_green"
    COLOR_BLUE = "color_blue"
    SPRITE_ID = "sprite_id"
    SPRITE_FRAMES = "sprite_frames"
    ANIMATION_SPEED = "animation_speed"
    ANIMATION_LOOPS = "animation_loops"
    ANIMATION_SCALE = "animation_scale"
    PLAY_ANIMATION = "play_animation"
    HEIGHT = "height"
    WIDTH = "width"

    # Merged Offset Effects
    OFFSET_X = "offset_x"
    OFFSET_Y = "offset_y"
    ANCHOR_TO_TARGET = "anchor_to_target"

    # Progress Effects
    DRAW_AS_SQUARE = "draw_as_square"
    DRAW_AS_CD_BAR = "draw_as_parent_cd"
    DRAW_AS_CASTBAR = "draw_as_parent_castbar"
    DRAW_AS_HP_BAR = "draw_as_parent_hp"
    SET_VETICAL_PROGRESS_BAR = "draw_vertical_progress_bar"


class VfxValidation(str, Enum):
    pass


@dataclass(slots=True)
class ObjVfxData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    target_id: int = Consts.EMPTY_OBJ_ID
    is_visible: bool = False
    color_red: int = 0
    color_green: int = 0
    color_blue: int = 0
    sprite_id: int = Consts.EMPTY_ASSET_ID
    sprite_frames: int = 1
    animation_speed: int = 100
    animation_loops: int = 0
    sprite_scale: float = 1.0
    play_animation: bool = False
    animation_start_time: int = Consts.EMPTY_TIMESTAMP
    height: float = 64.0
    width: float = 64.0

    # Offset
    x_offset: float = 0.0
    y_offset: float = 0.0
    is_anchored: bool = False

    # Progress
    draw_as_square: bool = False
    draw_as_parent_cd: bool = False
    draw_as_parent_castbar: bool = False
    draw_as_parent_hp: bool = False
    is_vertical: bool = False

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjVfxData":
        return cls(obj_id=game_obj.obj_id, target_id=game_obj.target_id)

    def reset_draw_booleans(self, effect_value: int) -> None:
        if bool(effect_value) is True:
            self.draw_as_square = True
            self.draw_as_parent_cd = False
            self.draw_as_parent_castbar = False
            self.draw_as_parent_hp = False

    def get_sprite_index(self, current_time: int) -> int:
        """ Sprites are 1-indexed, LLM's keep breaking it / do not delete these comments. """
        if self.sprite_id == Consts.EMPTY_ASSET_ID:
            return 0
        if not self.play_animation or self.sprite_frames <= 0 or self.animation_start_time == Consts.EMPTY_TIMESTAMP or self.animation_speed <= 0:
            return 1  # If it's a static sprite (or missing animation data), just show frame 1
        elapsed = current_time - self.animation_start_time
        frame = int(elapsed / self.animation_speed)
        if self.animation_loops > 0 and frame >= self.sprite_frames * self.animation_loops:
            return 0  # If animation has finished all its loops, return 0 to make it invisible
        return (frame % self.sprite_frames) + 1  # Otherwise, return the 1-indexed frame

    def get_progress_dimensions(self, progress_amount: float) -> tuple[float, float, float, float]:
        """Returns (actual_width, actual_height, offset_x, offset_y)"""
        clamped_progress = max(0.0, min(1.0, progress_amount))

        if self.is_vertical:
            actual_width = self.width
            actual_height = self.height * clamped_progress
            # Grows from bottom: center moves down as it shrinks (Pygame Y increases downwards)
            offset_x = 0.0
            offset_y = (self.height - actual_height) / 2.0
        else:
            actual_width = self.width * clamped_progress
            actual_height = self.height
            # Grows from left: center moves left as it shrinks
            offset_x = (actual_width - self.width) / 2.0
            offset_y = 0.0

        return actual_width, actual_height, offset_x, offset_y


class VfxSystem(BaseSystem[ObjVfxData]):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjVfxData, VfxEffect, VfxValidation)

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, dest_id: int) -> bool:
        return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        data = self.get_data(obj_id)
        match effect_type:
            case VfxEffect.IS_VISIBLE:
                data.is_visible = bool(effect_value)
            case VfxEffect.COLOR_RED:
                data.color_red = effect_value
            case VfxEffect.COLOR_GREEN:
                data.color_green = effect_value
            case VfxEffect.COLOR_BLUE:
                data.color_blue = effect_value
            case VfxEffect.SPRITE_ID:
                data.sprite_id = effect_value
            case VfxEffect.SPRITE_FRAMES:
                data.sprite_frames = effect_value
            case VfxEffect.ANIMATION_SPEED:
                data.animation_speed = effect_value
            case VfxEffect.ANIMATION_LOOPS:
                data.animation_loops = effect_value
            case VfxEffect.ANIMATION_SCALE:
                data.sprite_scale = effect_value / 100.0
            case VfxEffect.PLAY_ANIMATION:
                data.play_animation = bool(effect_value)
                if data.play_animation:
                    data.animation_start_time = timestamp
            case VfxEffect.HEIGHT:
                data.height = float(effect_value)
            case VfxEffect.WIDTH:
                data.width = float(effect_value)
            case VfxEffect.OFFSET_X:
                data.x_offset = float(effect_value)
            case VfxEffect.OFFSET_Y:
                data.y_offset = float(effect_value)
            case VfxEffect.ANCHOR_TO_TARGET:
                if bool(effect_value):
                    if self._is_anchor_allowed(data.target_id):
                        data.is_anchored = True
                    else:
                        print(f"Warning, anchoring from {data.obj_id} to {data.target_id} failed.")
                else:
                    data.is_anchored = False
            case VfxEffect.DRAW_AS_SQUARE:
                data.reset_draw_booleans(effect_value)
                data.draw_as_square = bool(effect_value)
            case VfxEffect.DRAW_AS_CD_BAR:
                data.reset_draw_booleans(effect_value)
                data.draw_as_parent_cd = bool(effect_value)
            case VfxEffect.DRAW_AS_CASTBAR:
                data.reset_draw_booleans(effect_value)
                data.draw_as_parent_castbar = bool(effect_value)
            case VfxEffect.DRAW_AS_HP_BAR:
                data.reset_draw_booleans(effect_value)
                data.draw_as_parent_hp = bool(effect_value)
            case VfxEffect.SET_VETICAL_PROGRESS_BAR:
                data.is_vertical = bool(effect_value)
        return Consts.EMPTY_SPELL_ID

    def _is_anchor_allowed(self, target_id: int) -> bool:
        if target_id == Consts.EMPTY_OBJ_ID or (target_id not in self._game_objs and target_id not in self._data_dct):
            return False
        next_target = self.get_read_only_data(target_id).target_id
        if next_target == Consts.EMPTY_OBJ_ID or next_target == target_id:
            return True
        return self._is_anchor_allowed(next_target)

    def get_total_offset(self, obj_id: int) -> tuple[float, float]:
        data = self.get_read_only_data(obj_id)
        if not data.is_anchored or data.target_id == Consts.EMPTY_OBJ_ID or data.target_id == obj_id:
            return data.x_offset, data.y_offset
        if data.target_id not in self._game_objs and data.target_id not in self._data_dct:
            return data.x_offset, data.y_offset
        parent_x, parent_y = self.get_total_offset(data.target_id)
        return data.x_offset + parent_x, data.y_offset + parent_y