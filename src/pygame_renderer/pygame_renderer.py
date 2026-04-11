import pygame
import math
import os
from typing import Optional, Final
from src.settings import Colors
from ._animation_manager import AnimationManager
from ._sprite_manager import SpriteManager
from ._window_manager import WindowManager
from ._audio_manager import AudioManager
from ._input_handler import InputHandler
from src.models.components.controls import KeyPresses


class PygameRenderer:
    """Main pygame rendering implementation, handling drawing, audio, and input"""

    def __init__(self) -> None:
        self._audio_manager = AudioManager()
        self._input_handler = InputHandler()
        self._animation_manager = AnimationManager()
        self._sprite_manager = SpriteManager()
        self._window_manager = WindowManager()
        self._fonts: dict[int, pygame.font.Font] = {}
        self._glow_img: Optional[pygame.Surface] = None  # Lazy init, requires pygame to be running
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

    def fetch_player_input(self) -> KeyPresses:
        return self._input_handler.fetch_player_input()

    def get_current_time(self) -> float:
        return pygame.time.get_ticks() / 1000.0

    # --- Frame boundary ---

    def begin_frame(self) -> None:
        self._frame_started = True
        self._draw_game_background()

    def end_frame(self) -> None:
        if not self._frame_started:
            raise RuntimeError("end_frame() called without begin_frame()")
        self._draw_fps_counter()
        pygame.display.flip()
        self._frame_started = False
        self._manage_fps()

    # --- Public draw interface ---

    def draw_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        """Draw a circle or sprite at normalized coordinates"""
        pixel_size = self._get_circle_pixel_size(scale)
        if asset_name:
            sprite_size = pixel_size * 2
            self._draw_sprite(pos_xy, (sprite_size, sprite_size), asset_name)
        else:
            screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
            pygame.draw.circle(self._get_screen(), color_rgb, screen_pos, pixel_size)

    def draw_blinking_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], time_ms: float, asset_name: Optional[str] = None) -> None:
        """Draw a circle with blinking/glowing effect"""
        if asset_name:
            pixel_size = self._get_circle_pixel_size(scale)
            sprite_size = pixel_size * 2
            self._draw_sprite(pos_xy, (sprite_size, sprite_size), asset_name)
            return

        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        base_size = self._get_circle_pixel_size(scale)

        # Flicker animation
        flicker_speed = 6.0
        phase = (pos_xy[0] * 7 + pos_xy[1] * 13) % (2 * math.pi)
        flicker = 0.5 + 0.5 * math.sin(time_ms * flicker_speed + phase)
        brightness = 0.7 + 0.3 * flicker
        size = int(base_size * (1.0 + 0.05 * flicker))

        # Adjusted color
        r, g, b = color_rgb
        color = (min(int(r * brightness), 255), min(int(g * brightness), 255), min(int(b * brightness), 255))

        # Bobbing animation
        bob_amplitude = 0.08 * base_size
        bob_offset_x = bob_amplitude * math.sin(time_ms * 2.0 + phase)
        bob_offset_y = bob_amplitude * 0.7 * math.sin(time_ms * 1.5 + phase + math.pi / 2)
        display_pos = (screen_pos[0] + bob_offset_x, screen_pos[1] + bob_offset_y)

        # Draw glow
        glow_size = int(base_size * 3.2 * (1.0 + 0.05 * flicker))
        if glow_size % 2 != 0:
            glow_size += 1

        glow_img = self._get_glow_img()
        glow = pygame.transform.smoothscale(glow_img, (glow_size, glow_size))
        glow_tinted = glow.copy()
        glow_tinted.fill(color + (0,), special_flags=pygame.BLEND_RGBA_ADD)

        SVG_OFFSET_X = -1
        SVG_OFFSET_Y = -1
        scaled_offset_x = int(SVG_OFFSET_X * (glow_size / glow_img.get_width()))
        scaled_offset_y = int(SVG_OFFSET_Y * (glow_size / glow_img.get_height()))
        top_left = (
            int(display_pos[0] - glow_size // 2) + scaled_offset_x,
            int(display_pos[1] - glow_size // 2) + scaled_offset_y
        )
        self._get_screen().blit(glow_tinted, top_left)

        # Draw main orb
        pygame.draw.circle(self._get_screen(), color, display_pos, size)

    def draw_rectangle(self, pos_xy: tuple[float, float], scale_xy: tuple[float, float], color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        """Draw a rectangle at normalized coordinates"""
        width = int(scale_xy[0] * self._window_manager.get_play_area_width())
        height = int(scale_xy[1] * self._window_manager.get_play_area_width())
        if asset_name:
            self._draw_sprite(pos_xy, (width, height), asset_name)
        else:
            screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
            rect = pygame.Rect(0, 0, width, height)
            rect.center = screen_pos
            pygame.draw.rect(self._get_screen(), color_rgb, rect)

    def draw_cooldown_overlay(self, pos_xy: tuple[float, float], scale: float, progress: float) -> None:
        """Draw radial cooldown indicator"""
        if progress >= 1.0:
            return

        screen_pos = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        size = self._get_circle_pixel_size(scale)

        angle = progress * 360
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 0, 0, 128), (size, size), size)

        if angle > 0:
            start_angle = -270
            end_angle = start_angle + angle
            pygame.draw.arc(
                surf,
                (0, 0, 0, 0),
                (0, 0, size * 2, size * 2),
                math.radians(start_angle),
                math.radians(end_angle),
                size
            )

        self._get_screen().blit(surf, (screen_pos[0] - size, screen_pos[1] - size))

    def play_animation(self, pos_xy: tuple[float, float], scale: float, asset_name: Optional[str] = None) -> None:
        if asset_name:
            self._animation_manager.play_animation(asset_name, pos_xy[0], pos_xy[1], scale)

    def display_text(self, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: Optional[str] = None) -> None:
        if text:
            self._draw_text(pos_xy, font_size, color_rgb, text)

    def play_sound(self, asset_name: Optional[str]) -> None:
        if asset_name:
            self._audio_manager.play_sound(asset_name)

    # --- Private helpers ---

    def _draw_game_background(self) -> None:
        self._get_screen().fill(Colors.BLACK)
        for rect in self._window_manager.get_border_rectangles():
            pygame.draw.rect(self._get_screen(), Colors.GREY, rect)

    def _draw_fps_counter(self) -> None:
        self._draw_text(pos_xy=(0.01, 0.98), font_size=24, color_rgb=(255, 255, 255), text=f"FPS: {self._fps}")

    def _draw_text(self, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: str) -> None:
        """Draw text at normalized coordinates"""
        font = self._get_font(font_size)
        text_surface = font.render(text, True, color_rgb)
        screen_x, screen_y = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        self._get_screen().blit(text_surface, (screen_x, screen_y))

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

    def _get_font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.SysFont('Arial', size)
        return self._fonts[size]

    def _get_circle_pixel_size(self, scale: float) -> int:
        return int(scale * min(self._window_manager.get_play_area_width(), self._window_manager.get_play_area_height()))

    def _get_glow_img(self) -> pygame.Surface:
        """Lazy init glow image, requires pygame to be running"""
        if self._glow_img is None:
            self._glow_img = self._load_glow_effect()
        return self._glow_img

    @staticmethod
    def _load_glow_effect() -> pygame.Surface:
        try:
            glow_img = pygame.image.load("assets/images/Food.svg").convert_alpha()
            PADDING = 2
            w, h = glow_img.get_size()
            padded = pygame.Surface((w + PADDING * 2, h + PADDING * 2), pygame.SRCALPHA)
            padded.blit(glow_img, (PADDING, PADDING))
            return padded
        except FileNotFoundError:
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 100), (32, 32), 32)
            return surf