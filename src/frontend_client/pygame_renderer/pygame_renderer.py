# pygame_rendering_framework.py
import pygame
import sys
import os
from typing import Optional, Protocol
from src.frontend_client.frontend_client import IRenderingFramework

class IDrawManager(Protocol):
    def draw_game_background(self) -> None: ...
    def set_screen_resolution(self, window_width: int, window_height) -> None: ...
    def draw_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], asset_name: Optional[str]) -> None: ...
    def draw_blinking_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], time_ms: float, asset_name: Optional[str]) -> None: ...
    def draw_rectangle(self, pos_xy: tuple[float, float], scale_xy: tuple[float, float], color_rgb: tuple[int, int, int], asset_name: Optional[str]) -> None: ...
    def draw_text(self, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: str) -> None: ...
    def play_animation(self, pos_xy: tuple[float, float], scale: float, asset_name: str) -> None: ...

class IInputReader(Protocol):
    def is_running(self) -> bool: ...
    def fetch_player_input(self) -> str: ...

class IAudioPlayer(Protocol):
    def play_sound(self, asset_name: str) -> None: ...

class PygameRenderer(IRenderingFramework):
    """Main implementation of IRenderingFramework using Pygame"""

    def __init__(self, input_reader: IInputReader, draw_manager: IDrawManager, audio_player: IAudioPlayer) -> None:
        self.input_handler = input_reader
        self.draw_manager = draw_manager
        self.audio_manager = audio_player
        self._target_fps = 165
        self._fps = 0
        self._clock: Optional[pygame.time.Clock] = None
        self._frame_started = False

    def launch_rendering_framework(self) -> None:
        pygame.init()
        self.draw_manager.set_screen_resolution(1920, 1080)

    def terminate_rendering_framework(self) -> None:
        pygame.quit()
    def is_running(self) -> bool:
        return self.input_handler.is_running()
    def fetch_player_input(self) -> str:
        return self.input_handler.fetch_player_input()
    def get_current_time(self) -> float:
        return pygame.time.get_ticks() / 1000.0

    def begin_frame(self) -> None:
        self._frame_started = True
        self.draw_manager.draw_game_background()
    def end_frame(self) -> None:
        if not self._frame_started:
            raise RuntimeError("end_frame() called without begin_frame()")
        self._draw_fps_counter()
        pygame.display.flip()
        self._frame_started = False
        self._manage_fps()

    def draw_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        self.draw_manager.draw_circle(pos_xy, scale, color_rgb, asset_name)
    def draw_blinking_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], time_ms: float, asset_name: Optional[str] = None) -> None:
        self.draw_manager.draw_blinking_circle(pos_xy, scale, color_rgb, time_ms, asset_name)
    def draw_rectangle(self, pos_xy: tuple[float, float], scale_xy: tuple[float, float], color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        self.draw_manager.draw_rectangle(pos_xy, scale_xy, color_rgb, asset_name)
    def play_animation(self, pos_xy: tuple[float, float], scale: float, asset_name: Optional[str] = None) -> None:
        if asset_name:
            self.draw_manager.play_animation(pos_xy, scale, asset_name)
    def display_text(self, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: Optional[str] = None) -> None:
        if text:
            self.draw_manager.draw_text(pos_xy, font_size, color_rgb, text)
    def play_sound(self, asset_name: Optional[str]) -> None:
        if asset_name:
            self.audio_manager.play_sound(asset_name)

    def _manage_fps(self) -> None:
        if self._clock is None:
            self._clock = pygame.time.Clock()  # Lazy init to fix pygame init ordering issues
        self._clock.tick(self._target_fps)  # Wait such that game doesn't go above the max FPS
        self._fps = int(self._clock.get_fps())

    def _draw_fps_counter(self) -> None:
        pos_xy = (0.01, 0.98)
        font_size = 24
        color_rgb = (255, 255, 255)
        self.display_text(pos_xy, font_size, color_rgb, f"FPS: {self._fps}")
