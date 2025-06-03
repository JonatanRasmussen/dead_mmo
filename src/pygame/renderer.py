import pygame
import math
from typing import ValuesView
from src.models.game_obj import GameObj
from src.config.color import Color
from src.pygame.window_manager import WindowManager
from src.pygame.sprite_manager import SpriteManager
from src.pygame.animation_manager import AnimationManager

class Renderer:
    def __init__(self, window_manager: WindowManager, sprite_manager: SpriteManager, animation_manager: AnimationManager):
        self.window_manager = window_manager
        self.sprite_manager = sprite_manager
        self.animation_manager = animation_manager
        self.font = pygame.font.SysFont('Arial', 30)

    def draw_frame(self, game_objs: ValuesView[GameObj], fps: int, ingame_time: float) -> None:
        """Draw a complete frame"""
        self._clear_screen()
        self._draw_borders()
        self._draw_game_objects(game_objs, ingame_time)
        self._draw_animations()  # Draw animations on top of game objects
        self._draw_fps(fps)
        pygame.display.flip()

    def _clear_screen(self) -> None:
        """Clear the screen with black"""
        self.window_manager.screen.fill(Color.BLACK)

    def _draw_borders(self) -> None:
        """Draw the game area borders"""
        top = int(self.window_manager.WINDOW_HEIGHT * self.window_manager.BORDER_TOP)
        bot = int(self.window_manager.WINDOW_HEIGHT * self.window_manager.BORDER_BOT)
        sides = int(self.window_manager.WINDOW_WIDTH * self.window_manager.BORDER_SIDES)

        # Draw border rectangles
        pygame.draw.rect(self.window_manager.screen, Color.GREY, (0, 0, self.window_manager.WINDOW_WIDTH, top))
        pygame.draw.rect(self.window_manager.screen, Color.GREY, (0, self.window_manager.WINDOW_HEIGHT - bot, self.window_manager.WINDOW_WIDTH, bot))
        pygame.draw.rect(self.window_manager.screen, Color.GREY, (0, 0, sides, self.window_manager.WINDOW_HEIGHT))
        pygame.draw.rect(self.window_manager.screen, Color.GREY, (self.window_manager.WINDOW_WIDTH - sides, 0, sides, self.window_manager.WINDOW_HEIGHT))

    def _draw_game_objects(self, game_objs: ValuesView[GameObj], ingame_time: float) -> None:
        """Draw all visible game objects"""
        for game_obj in game_objs:
            if not game_obj.is_visible:
                continue

            self._draw_game_object(game_obj, ingame_time)

    def _draw_game_object(self, game_obj: GameObj, ingame_time: float) -> None:
        """Draw a single game object"""
        pos = self.window_manager.world_to_screen_coords(game_obj.x, game_obj.y)
        size = int(game_obj.size * self.window_manager.PLAY_HEIGHT)

        # Check if the game object has a sprite
        if hasattr(game_obj, 'sprite_name') and game_obj.sprite_name:
            self._draw_sprite(game_obj, pos, size)
        else:
            # Fallback to circle drawing
            pygame.draw.circle(self.window_manager.screen, game_obj.color, pos, size)

        # Draw cooldown indicator
        self._draw_cooldown_indicator(game_obj, pos, size, ingame_time)

    def _draw_sprite(self, game_obj: GameObj, pos: tuple, size: int) -> None:
        """Draw a sprite for the game object"""
        sprite = self.sprite_manager.get_sprite(game_obj.sprite_name)

        # Scale sprite to match the desired size
        sprite_size = size * 2  # Diameter
        scaled_sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size))

        # Center the sprite on the position
        sprite_rect = scaled_sprite.get_rect(center=pos)
        self.window_manager.screen.blit(scaled_sprite, sprite_rect)

    def _draw_cooldown_indicator(self, game_obj: GameObj, pos: tuple, size: int, ingame_time: float) -> None:
        """Draw the radial cooldown indicator"""
        progress = game_obj.get_gcd_progress(ingame_time)
        if progress >= 1.0:  # Fully cooled down, no indicator needed
            return

        # Calculate the angle for the progress (0 to 360 degrees)
        angle = progress * 360

        # Create a surface for the cooldown overlay
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

        # Draw the darkened overlay
        pygame.draw.circle(surf, (0, 0, 0, 128), (size, size), size)

        if angle > 0:  # Draw the revealed portion
            # Convert angle to radians and adjust starting position
            start_angle = -270  # Start from 12 o'clock position
            end_angle = start_angle + angle

            # Draw the pie shape to reveal the underlying circle
            pygame.draw.arc(surf, (0, 0, 0, 0), (0, 0, size * 2, size * 2),
                           math.radians(start_angle), math.radians(end_angle), size)

        # Blit the overlay onto the main screen
        self.window_manager.screen.blit(surf, (pos[0] - size, pos[1] - size))

    def _draw_animations(self) -> None:
        """Draw all active animations"""
        self.animation_manager.render(self.window_manager.screen, self.window_manager)

    def _draw_fps(self, fps: int) -> None:
        """Draw the FPS counter"""
        fps_text = self.font.render(f"FPS: {fps}", True, Color.WHITE)
        self.window_manager.screen.blit(fps_text, (10, 10))