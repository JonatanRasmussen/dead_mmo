import pygame

class FPSManager:
    def __init__(self, target_fps: int = 60):
        self.clock = pygame.time.Clock()
        self.target_fps = target_fps
        self.fps = 0

    def tick(self) -> None:
        """Call this once per frame to maintain target FPS"""
        self.clock.tick(self.target_fps)
        self.fps = int(self.clock.get_fps())

    def get_fps(self) -> int:
        """Get the current FPS"""
        return self.fps

    def get_delta_time(self, last_time: int) -> tuple[float, int]:
        """Calculate delta time and return new current time"""
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - last_time) / 1000.0
        return delta_time, current_time