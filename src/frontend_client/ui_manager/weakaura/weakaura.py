from enum import Enum, auto
from typing import Iterable, Optional, Protocol
from dataclasses import dataclass
from src.frontend_client.ui_manager.ui_manager import IRenderAction

class RenderActionType(Enum):
    EMPTY = auto()
    CIRCLE = auto()
    RECTANGLE = auto()
    ANIMATION = auto()
    TEXT = auto()
    AUDIO = auto()

@dataclass(slots=True, frozen=True)
class RenderAction(IRenderAction):
    _render_action_type: RenderActionType = RenderActionType.EMPTY
    pos_xy: tuple[float, float] = (0.0, 0.0)
    scale_xy: tuple[float, float] = (1.0, 1.0)
    color_rgb: tuple[int, int, int] = (255, 255, 255)
    asset_filepath: Optional[str] = None
    text_to_display: Optional[str] = None

    def convert_scale_xy_to_scale(self) -> float:
        scale_x, scale_y = self.scale_xy
        return min(scale_x, scale_y)
    def convert_scale_xy_to_font_size(self) -> int:
        scale_x, scale_y = self.scale_xy
        return round(min(scale_x, scale_y))

    def is_type_circle(self) -> bool:
        return self._render_action_type == RenderActionType.CIRCLE
    def is_type_rectangle(self) -> bool:
        return self._render_action_type == RenderActionType.RECTANGLE
    def is_type_animation(self) -> bool:
        return self._render_action_type == RenderActionType.ANIMATION
    def is_type_text(self) -> bool:
        return self._render_action_type == RenderActionType.TEXT
    def is_type_audio(self) -> bool:
        return self._render_action_type == RenderActionType.AUDIO

