from typing import Iterable, Optional, Protocol
from src.game_loop import IFrontendClient
from src.models.events import FinalizedEvent
from src.models.components import GameObj

class IRenderAction(Protocol):
    pos_xy: tuple[float, float]
    scale_xy: tuple[float, float]
    color_rgb: tuple[int, int, int]
    asset_name: Optional[str]
    text_to_display: Optional[str]
    def convert_scale_xy_to_scale(self) -> float: ...
    def convert_scale_xy_to_font_size(self) -> int: ...
    def is_type_circle(self) -> bool: ...
    def is_type_rectangle(self) -> bool: ...
    def is_type_animation(self) -> bool: ...
    def is_type_text(self) -> bool: ...
    def is_type_audio(self) -> bool: ...

class IRenderingFramework(Protocol):
    def launch_rendering_framework(self) -> None: ...
    def terminate_rendering_framework(self) -> None: ...
    def is_running(self) -> bool: ...
    def fetch_player_input(self) -> str: ...
    def get_current_time(self) -> float: ...
    def begin_frame(self) -> None: ...
    def end_frame(self) -> None: ...
    def draw_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], asset_name: Optional[str]) -> None: ...
    def draw_blinking_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], time_ms: float, asset_name: Optional[str]) -> None: ...
    def draw_rectangle(self, pos_xy: tuple[float, float], scale_xy: tuple[float, float], color_rgb: tuple[int, int, int], asset_name: Optional[str]) -> None: ...
    def play_animation(self, pos_xy: tuple[float, float], scale: float, asset_name: Optional[str]) -> None: ...
    def display_text(self, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: Optional[str]) -> None: ...
    def play_sound(self, asset_name: Optional[str]) -> None: ...

class IUiManager(Protocol):
    def apply_ui_update(self, serialized_event: str) -> None: ...
    def clear_current_frame_event_cache(self) -> None: ...
    def get_render_actions(self) -> Iterable[IRenderAction]: ...

class FrontendClient(IFrontendClient):

    def __init__(self, renderer: IRenderingFramework, ui_manager: IUiManager) -> None:
        self._rendering_framework = renderer
        self._ui_manager = ui_manager
        self._cached_time = self._rendering_framework.get_current_time()
        self._temp_game_state_serialized_objs: list[str] = []

    def launch_rendering_framework(self) -> None:
        self._rendering_framework.launch_rendering_framework()
    def terminate_rendering_framework(self) -> None:
        self._rendering_framework.terminate_rendering_framework()
    def is_running(self) -> bool:
        return self._rendering_framework.is_running()

    def fetch_player_input(self) -> str:
        return self._rendering_framework.fetch_player_input()

    def get_elapsed_time(self) -> float:
        current_time = self._rendering_framework.get_current_time()
        elapsed_time = current_time - self._cached_time
        self._cached_time = current_time
        return elapsed_time

    def apply_events(self, serialized_events: list[str]) -> None:
        for serialized_event in serialized_events:
            self._ui_manager.apply_ui_update(serialized_event)
            f_event = FinalizedEvent.deserialize(serialized_event)
            if f_event.should_play_audio:
                self._rendering_framework.play_sound(f_event.audio_name)
            if f_event.should_play_animation:
                pos = (f_event.effect_position.x, f_event.effect_position.y)
                self._rendering_framework.play_animation(
                    pos_xy=pos,
                    scale=f_event.animation_scale,
                    asset_name=f_event.animation_name
                )

    def render_frame(self) -> None:
        self._rendering_framework.begin_frame()
        self._render_frame_actions()
        self._rendering_framework.end_frame()

    def _render_frame_actions(self) -> None:
        # temp obj draw logic, remove later
        for serialized_obj in self._temp_game_state_serialized_objs:
            game_obj = GameObj.deserialize(serialized_obj)
            if game_obj.is_visible:
                pos = (game_obj.pos.x, game_obj.pos.y)
                asset = game_obj.sprite_name if game_obj.should_render_sprite else None
                self._rendering_framework.draw_blinking_circle(
                    pos_xy=pos,
                    scale=game_obj.size,
                    color_rgb=game_obj.color,
                    time_ms=self._rendering_framework.get_current_time(),
                    asset_name=asset
                )
        # continue with the proper (but not yet implemented) logic
        for rend_act in self._ui_manager.get_render_actions():
            if rend_act.is_type_circle():
                scale = rend_act.convert_scale_xy_to_scale()
                self._rendering_framework.draw_circle(rend_act.pos_xy, scale, rend_act.color_rgb, rend_act.asset_name)
            elif rend_act.is_type_rectangle():
                self._rendering_framework.draw_rectangle(rend_act.pos_xy, rend_act.scale_xy, rend_act.color_rgb, rend_act.asset_name)
            elif rend_act.is_type_animation():
                scale = rend_act.convert_scale_xy_to_scale()
                self._rendering_framework.play_animation(rend_act.pos_xy, scale, rend_act.asset_name)
            elif rend_act.is_type_text():
                font_size = rend_act.convert_scale_xy_to_font_size()
                self._rendering_framework.display_text(rend_act.pos_xy, font_size, rend_act.color_rgb, rend_act.text_to_display)
            elif rend_act.is_type_audio():
                self._rendering_framework.play_sound(rend_act.asset_name)
        #Prepare for next frame
        self._ui_manager.clear_current_frame_event_cache()

    def apply_serialized_game_state(self, serialized_objs: list[str]) -> None:
        self._temp_game_state_serialized_objs.clear()
        self._temp_game_state_serialized_objs = serialized_objs