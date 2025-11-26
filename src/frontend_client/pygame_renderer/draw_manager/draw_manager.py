# draw_manager.py
import pygame
import math
import os
from typing import Optional, Protocol
from src.frontend_client.pygame_renderer.pygame_renderer import IDrawManager
from src.settings import Colors

class IWindowManager(Protocol):
    def set_window_resolution(self, window_width: int, window_height) -> None: ...
    def get_border_rectangles(self) -> list[tuple[int, int, int, int]]: ...
    def calculate_play_area(self) -> None: ...
    def world_to_screen_coords(self, x: float, y: float) -> tuple[int, int]: ...
    def get_play_area_width(self) -> float: ...
    def get_play_area_height(self) -> float: ...

class ISpriteManager(Protocol):
    def get_sprite(self, asset_name: str) -> pygame.Surface: ...

class IAnimationManager(Protocol):
    def play_animation(self, animation_name: str, x: float, y: float, scale: float = 1.0) -> None: ...

class DrawManager(IDrawManager):
    """Handles all drawing operations"""

    def __init__(self, window_manager: IWindowManager, sprite_manager: ISpriteManager, animation_manager: IAnimationManager):
        self.window_manager = window_manager
        self.sprite_manager = sprite_manager
        self.animation_manager = animation_manager
        self.fonts: dict[int, pygame.font.Font] = {}
        self.glow_img = self._load_glow_effect()

    def draw_game_background(self):
        self._get_screen().fill(Colors.BLACK)  # Draw background
        border_rects = self.window_manager.get_border_rectangles()  # Draw borders
        for rect in border_rects:
            pygame.draw.rect(self._get_screen(), Colors.GREY, rect)

    def set_screen_resolution(self, window_width: int, window_height) -> None:
        self.window_manager.set_window_resolution(window_width, window_height)

    def draw_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        """Draw a circle or sprite at normalized coordinates"""
        pixel_size = self._get_circle_pixel_size(scale)
        if asset_name:
            sprite_size = pixel_size * 2
            self._draw_sprite(pos_xy, (sprite_size, sprite_size), asset_name)
        else:
            screen_pos = self.window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
            pygame.draw.circle(self._get_screen(), color_rgb, screen_pos, pixel_size)

    def draw_blinking_circle(self, pos_xy: tuple[float, float], scale: float, color_rgb: tuple[int, int, int], time_ms: float, asset_name: Optional[str] = None) -> None:
        """Draw a circle with blinking/glowing effect"""

        if asset_name:
            # Draw sprite without blinking effect
            pixel_size = self._get_circle_pixel_size(scale)
            sprite_size = pixel_size * 2
            self._draw_sprite(pos_xy, (sprite_size, sprite_size), asset_name)
            return

        screen_pos = self.window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        base_size = self._get_circle_pixel_size(scale)

        # Flicker animation
        flicker_speed = 6.0
        phase = (pos_xy[0] * 7 + pos_xy[1] * 13) % (2 * math.pi)
        flicker = 0.5 + 0.5 * math.sin(time_ms * flicker_speed + phase)
        brightness = 0.7 + 0.3 * flicker
        size = int(base_size * (1.0 + 0.05 * flicker))

        # Adjusted color
        r, g, b = color_rgb
        color = (min(int(r * brightness), 255), min(int(g * brightness), 255),min(int(b * brightness), 255))

        # Bobbing animation
        bob_amplitude = 0.08 * base_size
        bob_speed_x = 2.0
        bob_speed_y = 1.5
        bob_offset_x = bob_amplitude * math.sin(time_ms * bob_speed_x + phase)
        bob_offset_y = bob_amplitude * 0.7 * math.sin(time_ms * bob_speed_y + phase + math.pi / 2)

        display_pos = (screen_pos[0] + bob_offset_x, screen_pos[1] + bob_offset_y)

        # Draw glow
        glow_size = int(base_size * 3.2 * (1.0 + 0.05 * flicker))
        if glow_size % 2 != 0:
            glow_size += 1

        glow = pygame.transform.smoothscale(self.glow_img, (glow_size, glow_size))
        glow_tinted = glow.copy()
        glow_tinted.fill(color + (0,), special_flags=pygame.BLEND_RGBA_ADD)

        SVG_OFFSET_X = -1
        SVG_OFFSET_Y = -1
        scaled_offset_x = int(SVG_OFFSET_X * (glow_size / self.glow_img.get_width()))
        scaled_offset_y = int(SVG_OFFSET_Y * (glow_size / self.glow_img.get_height()))

        top_left = (
            int(display_pos[0] - glow_size // 2) + scaled_offset_x,
            int(display_pos[1] - glow_size // 2) + scaled_offset_y
        )
        self._get_screen().blit(glow_tinted, top_left)

        # Draw main orb
        pygame.draw.circle(self._get_screen(), color, display_pos, size)

    def draw_rectangle(self, pos_xy: tuple[float, float], scale_xy: tuple[float, float], color_rgb: tuple[int, int, int], asset_name: Optional[str] = None) -> None:
        """Draw a rectangle at normalized coordinates"""
        # Convert scale to pixel size
        width = int(scale_xy[0] * self.window_manager.get_play_area_width())
        height = int(scale_xy[1] * self.window_manager.get_play_area_width())

        if asset_name:
            # Draw textured rectangle
            self._draw_sprite(pos_xy, (width, height), asset_name)
        else:
            # Draw solid rectangle
            screen_pos = self.window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
            rect = pygame.Rect(0, 0, width, height)
            rect.center = screen_pos
            pygame.draw.rect(self._get_screen(), color_rgb, rect)

    def draw_cooldown_overlay(self, pos_xy: tuple[float, float], scale: float, progress: float) -> None:
        """Draw radial cooldown indicator"""
        if progress >= 1.0:
            return

        screen_pos = self.window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
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

    def draw_text(self, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: str) -> None:
        """Draw text at normalized coordinates"""
        font = self._get_font(font_size)
        text_surface = font.render(text, True, color_rgb)
        screen_x, screen_y = self.window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        self._get_screen().blit(text_surface, (screen_x, screen_y))

    def play_animation(self, pos_xy: tuple[float, float], scale: float, asset_name: str) -> None:
        """Draw all active animations"""
        self.animation_manager.play_animation(asset_name, pos_xy[0], pos_xy[1], scale)

    # Helper methods

    def _get_screen(self) -> pygame.Surface:
        return pygame.display.get_surface()

    def _get_font(self, size: int) -> pygame.font.Font:
        """Get or create a font of the specified size"""
        if size not in self.fonts:
            self.fonts[size] = pygame.font.SysFont('Arial', size)
        return self.fonts[size]

    def _get_circle_pixel_size(self, scale: float) -> int:
        return int(scale * min(self.window_manager.get_play_area_width(), self.window_manager.get_play_area_height()))

    def _draw_sprite(self, pos_xy: tuple[float, float], size: tuple[int, int], asset_name: str) -> None:
        """Draw a sprite at normalized coordinates with given pixel size"""
        screen_pos = self.window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])
        sprite = self.sprite_manager.get_sprite(asset_name)
        scaled_sprite = pygame.transform.scale(sprite, size)
        sprite_rect = scaled_sprite.get_rect(center=screen_pos)
        self._get_screen().blit(scaled_sprite, sprite_rect)

    @staticmethod
    def _load_glow_effect() -> pygame.Surface:
        """Load the glow effect image"""
        try:
            glow_img = pygame.image.load("assets/images/Food.svg").convert_alpha()
            PADDING = 2
            w, h = glow_img.get_size()
            padded_glow_image = pygame.Surface((w + PADDING * 2, h + PADDING * 2), pygame.SRCALPHA)
            padded_glow_image.blit(glow_img, (PADDING, PADDING))
            return padded_glow_image
        except FileNotFoundError:
            # Return a default glow surface if file not found
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 100), (32, 32), 32)
            return surf