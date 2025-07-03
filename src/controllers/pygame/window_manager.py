import pygame
from typing import Tuple

class WindowManager:
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
        screen_y = self.BORDER_TOP * self.WINDOW_HEIGHT + (1 - y) * self.PLAY_HEIGHT
        return (int(screen_x), int(screen_y))

    def get_play_area_size(self) -> tuple[float, float]:
        """Returns the play area dimensions"""
        return (self.PLAY_WIDTH, self.PLAY_HEIGHT)
