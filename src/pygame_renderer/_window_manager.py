import pygame

class WindowManager:
    def __init__(self, width: int = 1920, height: int = 1080):
        self.WINDOW_WIDTH = width
        self.WINDOW_HEIGHT = height

        self.LOGICAL_WIDTH: float = 1920.0
        self.LOGICAL_HEIGHT: float = 1080.0

        self.PLAY_WIDTH: float = 0.0
        self.PLAY_HEIGHT: float = 0.0
        self.OFFSET_X: float = 0.0
        self.OFFSET_Y: float = 0.0

        self.screen: pygame.Surface = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Dead MMO")

        self.camera_pos_xy: tuple[float, float] = (0.0, 0.0)

        self.calculate_play_area()

    def set_window_resolution(self, window_width: int, window_height: int) -> None:
        self.WINDOW_WIDTH = window_width
        self.WINDOW_HEIGHT = window_height
        pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        self.calculate_play_area()

    def set_camera_position(self, pos_xy: tuple[float, float]) -> None:
        self.camera_pos_xy = pos_xy

    def get_border_rectangles(self) -> list[tuple[int, int, int, int]]:
        """Returns list of (x, y, width, height) tuples for border rectangles"""
        rects = []
        if self.OFFSET_Y > 0:
            rects.append((0, 0, self.WINDOW_WIDTH, int(self.OFFSET_Y)))
            rects.append((0, int(self.WINDOW_HEIGHT - self.OFFSET_Y), self.WINDOW_WIDTH, int(self.OFFSET_Y)))
        if self.OFFSET_X > 0:
            rects.append((0, 0, int(self.OFFSET_X), self.WINDOW_HEIGHT))
            rects.append((int(self.WINDOW_WIDTH - self.OFFSET_X), 0, int(self.OFFSET_X), self.WINDOW_HEIGHT))
        return rects

    def calculate_play_area(self) -> None:
        logical_ratio = self.LOGICAL_WIDTH / self.LOGICAL_HEIGHT
        window_ratio = self.WINDOW_WIDTH / self.WINDOW_HEIGHT

        if window_ratio > logical_ratio:
            self.PLAY_HEIGHT = self.WINDOW_HEIGHT
            self.PLAY_WIDTH = self.PLAY_HEIGHT * logical_ratio
            self.OFFSET_X = (self.WINDOW_WIDTH - self.PLAY_WIDTH) / 2
            self.OFFSET_Y = 0
        else:
            self.PLAY_WIDTH = self.WINDOW_WIDTH
            self.PLAY_HEIGHT = self.PLAY_WIDTH / logical_ratio
            self.OFFSET_X = 0
            self.OFFSET_Y = (self.WINDOW_HEIGHT - self.PLAY_HEIGHT) / 2

    def world_to_screen_coords(self, x: float, y: float) -> tuple[int, int]:
        """Convert from world coordinates to screen coordinates, relative to the camera"""
        cam_x, cam_y = self.camera_pos_xy

        dist_x = x - cam_x
        dist_y = y - cam_y

        scale = self.PLAY_WIDTH / self.LOGICAL_WIDTH
        screen_dist_x = dist_x * scale
        screen_dist_y = dist_y * scale

        screen_center_x = self.OFFSET_X + self.PLAY_WIDTH / 2
        screen_center_y = self.OFFSET_Y + self.PLAY_HEIGHT / 2

        screen_x = screen_center_x + screen_dist_x
        screen_y = screen_center_y - screen_dist_y

        return (int(screen_x), int(screen_y))

    def ui_to_screen_coords(self, x: float, y: float) -> tuple[int, int]:
        """Convert from normalized UI coordinates (0-1) to fixed screen coordinates"""
        screen_x = self.OFFSET_X + x * self.PLAY_WIDTH
        screen_y = self.OFFSET_Y + (1 - y) * self.PLAY_HEIGHT
        return (int(screen_x), int(screen_y))

    def get_play_area_width(self) -> float:
        return self.PLAY_WIDTH

    def get_play_area_height(self) -> float:
        return self.PLAY_HEIGHT

    def get_logical_width(self) -> float:
        return self.LOGICAL_WIDTH