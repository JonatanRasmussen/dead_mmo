import pygame
from src.frontend_client.pygame_renderer.draw_manager.draw_manager import IWindowManager

class WindowManager(IWindowManager):
    def __init__(self, width: int = 1920, height: int = 1080):
        self.WINDOW_WIDTH = width
        self.WINDOW_HEIGHT = height

        self.PLAY_WIDTH: float = 0.0
        self.PLAY_HEIGHT: float = 0.0
        self.movement_adjustment_x: float = 0.0
        self.movement_adjustment_y: float = 0.0

        self.BORDER_TOP: float = 0.1
        self.BORDER_BOT: float = 0.2
        self.BORDER_SIDES: float = 0.05
        self.PLAY_RATIO: float = 1 / 1

        self.screen: pygame.Surface = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Dead MMO")

        self.calculate_play_area()

    def set_window_resolution(self, window_width: int, window_height) -> None:
        self.WINDOW_WIDTH = window_width
        self.WINDOW_HEIGHT = window_height
        pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Dead MMO")

    def get_border_rectangles(self) -> list[tuple[int, int, int, int]]:
        """Returns list of (x, y, width, height) tuples for border rectangles"""
        top = int(self.WINDOW_HEIGHT * self.BORDER_TOP)
        bot = int(self.WINDOW_HEIGHT * self.BORDER_BOT)
        sides = int(self.WINDOW_WIDTH * self.BORDER_SIDES)

        return [
            (0, 0, self.WINDOW_WIDTH, top),  # Top border
            (0, self.WINDOW_HEIGHT - bot, self.WINDOW_WIDTH, bot),  # Bottom border
            (0, 0, sides, self.WINDOW_HEIGHT),  # Left border
            (self.WINDOW_WIDTH - sides, 0, sides, self.WINDOW_HEIGHT)  # Right border
        ]

    def calculate_play_area(self) -> None:
        # Calculate maximum possible play area dimensions considering minimum borders
        max_play_width = self.WINDOW_WIDTH * (1 - 2 * self.BORDER_SIDES)
        max_play_height = self.WINDOW_HEIGHT * (1 - self.BORDER_TOP - self.BORDER_BOT)

        # Calculate actual play area dimensions maintaining ratio
        if max_play_width / max_play_height > self.PLAY_RATIO:
            # Too wide, adjust width
            self.PLAY_HEIGHT = max_play_height
            self.PLAY_WIDTH = self.PLAY_HEIGHT * self.PLAY_RATIO
            # Center horizontally with extra border
            extra_width = max_play_width - self.PLAY_WIDTH
            self.BORDER_SIDES += extra_width / (2 * self.WINDOW_WIDTH)
        else:
            # Too tall, adjust height
            self.PLAY_WIDTH = max_play_width
            self.PLAY_HEIGHT = self.PLAY_WIDTH / self.PLAY_RATIO
            # Center vertically with extra border
            extra_height = max_play_height - self.PLAY_HEIGHT
            extra_top = extra_height / 2
            self.BORDER_TOP += extra_top / self.WINDOW_HEIGHT
            self.BORDER_BOT += extra_top / self.WINDOW_HEIGHT

        # Calculate movement speed adjustment factors
        aspect_ratio = self.PLAY_WIDTH / self.PLAY_HEIGHT
        if aspect_ratio > 1:
            # Wider than tall - adjust horizontal movement
            self.movement_adjustment_x = 1.0 / aspect_ratio
            self.movement_adjustment_y = 1.0
        else:
            # Taller than wide - adjust vertical movement
            self.movement_adjustment_x = 1.0
            self.movement_adjustment_y = aspect_ratio

    def world_to_screen_coords(self, x: float, y: float) -> tuple[int, int]:
        """Convert from unit coordinates (0-1) to screen coordinates"""
        screen_x = self.BORDER_SIDES * self.WINDOW_WIDTH + x * self.PLAY_WIDTH
        screen_y = self.BORDER_TOP * self.WINDOW_HEIGHT + (1 - y) * self.PLAY_HEIGHT  # (1 - y) fixes offset bug
        return (int(screen_x), int(screen_y))

    def get_play_area_width(self) -> float:
        return self.PLAY_WIDTH

    def get_play_area_height(self) -> float:
        return self.PLAY_HEIGHT