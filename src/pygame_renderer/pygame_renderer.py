import pygame
import math
import os
from typing import Optional, Final
from src.settings import Colors, Consts
from ._animation_manager import AnimationManager
from ._sprite_manager import SpriteManager
from ._window_manager import WindowManager
from ._audio_manager import AudioManager
from ._input_handler import InputHandler
from ._glow_manager import GlowManager
from ._text_manager import TextManager


class PygameRenderer:
    """Main pygame rendering implementation, handling drawing, audio, and input"""

    def __init__(self) -> None:
        self._audio_manager = AudioManager()
        self._input_handler = InputHandler()
        self._animation_manager = AnimationManager()
        self._sprite_manager = SpriteManager()
        self._window_manager = WindowManager()
        self._glow_manager = GlowManager()
        self._text_manager = TextManager(self._window_manager)

        self._target_fps = 165
        self._fps = 0
        self._clock: Optional[pygame.time.Clock] = None  # Lazy init, requires pygame to be running
        self._frame_started = False

    @property
    def target_fps(self) -> int:
        return self._target_fps

    # --- Lifecycle ---

    def launch_rendering_framework(self) -> None:
        pygame.init()
        self._window_manager.set_window_resolution(1920, 1080)

    def terminate_rendering_framework(self) -> None:
        pygame.quit()

    def is_running(self) -> bool:
        return self._input_handler.is_running()

    def fetch_player_input(self) -> list[str]:
        return self._input_handler.fetch_player_input()

    def get_current_time(self) -> float:
        return pygame.time.get_ticks() / Consts.TIMESTAMPS_PER_SECOND

    def set_camera_position(self, pos_xy: tuple[float, float]) -> None:
        self._window_manager.set_camera_position(pos_xy)

    # --- Frame boundary ---

    def begin_frame(self) -> None:
        self._frame_started = True
        self._get_screen().fill(Colors.BLACK)
        #self._draw_game_background()

    def end_frame(self) -> None:
        if not self._frame_started:
            raise RuntimeError("end_frame() called without begin_frame()")
        for rect in self._window_manager.get_border_rectangles():
            pygame.draw.rect(self._get_screen(), Colors.GREY, rect)
        self._draw_fps_counter()
        pygame.display.flip()
        self._frame_started = False
        self._manage_fps()

    # --- Public draw interface ---

    def draw_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        """Draw a circle or sprite at normalized coordinates"""
        pixel_size = self._get_circle_pixel_size(scale)
        if asset_name:
            self._draw_sprite(pos_xy, (pixel_size, pixel_size), asset_name)
        else:
            screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
            pygame.draw.circle(self._get_screen(), color_rgb, screen_pos, int(pixel_size / 2))

    def draw_rectangle(self, pos_xy: tuple[float, float], scale_xy: tuple[float, float], color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        """Draw a solid rectangle at normalized coordinates"""
        width_px = self._get_circle_pixel_size(scale_xy[0])
        height_px = self._get_circle_pixel_size(scale_xy[1])
        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        rect = pygame.Rect(0, 0, width_px, height_px)
        rect.center = screen_pos

        if asset_name:
            self._draw_sprite(pos_xy, (width_px, height_px), asset_name)
        else:
            pygame.draw.rect(self._get_screen(), color_rgb, rect)

    def draw_blinking_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], time_ms: float, asset_name: Optional[str] = None, glow_radius_multiplier: float = 4.0) -> None:
        """Draw a circle with a glowing/blinking effect (supports both old SVG and new Neon)"""
        if asset_name:
            pixel_size = self._get_circle_pixel_size(scale)
            self._draw_sprite(pos_xy, (pixel_size, pixel_size), asset_name)
            return

        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        base_size = self._get_circle_pixel_size(scale)
        if base_size <= 0:
            return

        flicker_speed = 6.0
        phase = ((pos_xy[0] / 1000.0) * 7 + (pos_xy[1] / 1000.0) * 13) % (2 * math.pi)
        flicker = 0.5 + 0.5 * math.sin(time_ms * flicker_speed + phase)

        bob_amplitude = 0.08 * base_size
        bob_offset_x = bob_amplitude * math.sin(time_ms * 2.0 + phase)
        bob_offset_y = bob_amplitude * 0.7 * math.sin(time_ms * 1.5 + phase + math.pi / 2)
        display_pos = (int(screen_pos[0] + bob_offset_x), int(screen_pos[1] + bob_offset_y))

        # --- NEON LOGIC (Optimized with Scaled Cache) ---
        glow_radius = int((base_size / 2) * glow_radius_multiplier * (0.95 + 0.1 * flicker))
        glow_diameter = max(2, glow_radius * 2)

        # Pass 1: Blit the wide soft halo with additive blending
        scaled_glow = self._glow_manager.get_scaled_neon_glow(color_rgb, glow_diameter)
        glow_rect = scaled_glow.get_rect(center=display_pos)
        self._get_screen().blit(scaled_glow, glow_rect, special_flags=pygame.BLEND_ADD)

        # Pass 2: Blit a smaller, concentrated version at the center for a super-bright core
        inner_diameter = max(2, int(base_size * 1.1))
        inner_glow = self._glow_manager.get_scaled_neon_glow(color_rgb, inner_diameter)
        inner_rect = inner_glow.get_rect(center=display_pos)
        self._get_screen().blit(inner_glow, inner_rect, special_flags=pygame.BLEND_ADD)

    def draw_neon_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], asset_name: Optional[str] = None, glow_radius_multiplier: float = 4.0) -> None:
        """Draws a static neon circle with a hot core and additive glowing halo."""
        if asset_name:
            pixel_size = self._get_circle_pixel_size(scale)
            self._draw_sprite(pos_xy, (pixel_size, pixel_size), asset_name)
            return

        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        base_size = self._get_circle_pixel_size(scale)

        if base_size <= 0:
            return

        # Size of the total glow aura
        glow_radius = int((base_size / 2) * glow_radius_multiplier)
        glow_diameter = max(2, glow_radius * 2)

        # Pass 1: Blit the wide soft halo with additive blending
        scaled_glow = self._glow_manager.get_scaled_neon_glow(color_rgb, glow_diameter)
        glow_rect = scaled_glow.get_rect(center=screen_pos)
        self._get_screen().blit(scaled_glow, glow_rect, special_flags=pygame.BLEND_ADD)

        # Pass 2: Blit a smaller, concentrated version at the center for a super-bright core
        inner_diameter = max(2, int(base_size * 1.1))
        inner_glow = self._glow_manager.get_scaled_neon_glow(color_rgb, inner_diameter)
        inner_rect = inner_glow.get_rect(center=screen_pos)
        self._get_screen().blit(inner_glow, inner_rect, special_flags=pygame.BLEND_ADD)

    def draw_cooldown_overlay(self, pos_xy: tuple[float, float], scale: float, progress: float) -> None:
        """Draw radial cooldown indicator"""
        if progress >= 1.0:
            return

        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        size = self._get_circle_pixel_size(scale)
        radius = int(size / 2)

        angle = progress * 360
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 0, 0, 128), (radius, radius), radius)

        if angle > 0:
            start_angle = -270
            end_angle = start_angle + angle
            pygame.draw.arc(
                surf,
                (0, 0, 0, 0),
                (0, 0, size, size),
                math.radians(start_angle),
                math.radians(end_angle),
                radius
            )

        self._get_screen().blit(surf, (screen_pos[0] - radius, screen_pos[1] - radius))

    def draw_animation(self, pos_xy: tuple[float, float], scale: float, asset_name: str, elapsed_time_ms: float, ms_per_frame: Optional[float] = None, alpha: float = 1.0, loop: bool = False) -> None:
        frame_surface = self._animation_manager.get_frame_at_time(asset_name, elapsed_time_ms, loop, ms_per_frame)
        if not frame_surface:
            return
        pixel_size = self._get_circle_pixel_size(scale)
        scaled_frame = pygame.transform.scale(frame_surface, (pixel_size, pixel_size))
        if alpha < 1.0:
            scaled_frame.set_alpha(int(alpha * 255))
        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        sprite_rect = scaled_frame.get_rect(center=screen_pos)
        self._get_screen().blit(scaled_frame, sprite_rect)

    def display_text(self, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: Optional[str] = None, is_ui: bool = False) -> None:
        if text:
            self._text_manager.draw_text(self._get_screen(), pos_xy, font_size, color_rgb, text, is_ui)

    def play_sound(self, asset_name: Optional[str]) -> None:
        if asset_name:
            self._audio_manager.play_sound(asset_name)

    def update_audio(self, obj_id: int, audio_name: str, audio_start: int, audio_loop: bool, frame_start: int) -> None:
        self._audio_manager.update_audio(obj_id, audio_name, audio_start, audio_loop, frame_start)

    # --- Private helpers ---

    def _draw_game_background(self) -> None:
        self._get_screen().fill(Colors.BLACK)
        for rect in self._window_manager.get_border_rectangles():
            pygame.draw.rect(self._get_screen(), Colors.GREY, rect)

    def _draw_fps_counter(self) -> None:
        self._text_manager.draw_text(self._get_screen(), pos_xy=(0.01, 0.98), font_size=24, color_rgb=(255, 255, 255), text=f"FPS: {self._fps}", is_ui=True)

    def _draw_sprite(self, pos_xy: tuple[float, float], size: tuple[int, int], asset_name: str) -> None:
        """Draw a sprite at normalized coordinates with given pixel size"""
        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        sprite = self._sprite_manager.get_sprite(asset_name)
        scaled_sprite = pygame.transform.scale(sprite, size)
        sprite_rect = scaled_sprite.get_rect(center=screen_pos)
        self._get_screen().blit(scaled_sprite, sprite_rect)

    def _manage_fps(self) -> None:
        if self._clock is None:
            self._clock = pygame.time.Clock()
        self._clock.tick(self._target_fps)
        self._fps = int(self._clock.get_fps())

    def _get_screen(self) -> pygame.Surface:
        return pygame.display.get_surface()

    def _get_circle_pixel_size(self, scale: float) -> int:
        pixel_scale = self._window_manager.get_play_area_width() / self._window_manager.get_logical_width()
        return int(scale * pixel_scale)