import pygame
from ._window_manager import WindowManager

class TextManager:
    """Handles font caching and text rendering."""

    def __init__(self, window_manager: WindowManager) -> None:
        self._window_manager = window_manager
        self._fonts: dict[int, pygame.font.Font] = {}

    def get_font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.SysFont('Arial', size)
        return self._fonts[size]

    def draw_text(self, screen: pygame.Surface, pos_xy: tuple[float, float], font_size: int, color_rgb: tuple[int, int, int], text: str, is_ui: bool = False) -> None:
        """Draw text at normalized coordinates"""
        pixel_scale = self._window_manager.get_play_area_width() / self._window_manager.get_logical_width()
        scaled_font_size = max(1, int(font_size * pixel_scale))
        font = self.get_font(scaled_font_size)
        text_surface = font.render(text, True, color_rgb)

        if is_ui:
            screen_x, screen_y = self._window_manager.ui_to_screen_coords(pos_xy[0], pos_xy[1])
        else:
            screen_x, screen_y = self._window_manager.world_to_screen_coords(pos_xy[0], pos_xy[1])

        screen.blit(text_surface, (screen_x, screen_y))