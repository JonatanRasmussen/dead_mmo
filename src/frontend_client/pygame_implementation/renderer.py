import pygame
import math
from typing import ValuesView
from src.models.components import GameObj
from src.settings import Colors
from .window_manager import WindowManager
from .sprite_manager import SpriteManager
from .animation_manager import AnimationManager

class Renderer:
    def __init__(self, window_manager: WindowManager, sprite_manager: SpriteManager, animation_manager: AnimationManager):
        self.window_manager = window_manager
        self.sprite_manager = sprite_manager
        self.animation_manager = animation_manager
        self.font = pygame.font.SysFont('Arial', 30)
        #self.glow_img = pygame.image.load("assets/images/Food.svg").convert_alpha()
        #pygame.draw.rect(self.glow_img, (255, 0, 0), self.glow_img.get_rect(), 1)  # red border
        self.glow_img = self._load_glow_effect()

    def draw_frame(self, game_objs: ValuesView[GameObj], fps: int, ingame_time: int) -> None:
        """Draw a complete frame"""
        self._clear_screen()
        self._draw_borders()
        #self._draw_game_objects(game_objs, ingame_time)
        self._draw_blinking_game_objects(game_objs, ingame_time)
        self._draw_animations()  # Draw animations on top of game objects
        self._draw_fps(fps)
        pygame.display.flip()

    def _clear_screen(self) -> None:
        """Clear the screen with black"""
        self.window_manager.screen.fill(Colors.BLACK)

    def _draw_borders(self) -> None:
        """Draw the game area borders"""
        top = int(self.window_manager.WINDOW_HEIGHT * self.window_manager.BORDER_TOP)
        bot = int(self.window_manager.WINDOW_HEIGHT * self.window_manager.BORDER_BOT)
        sides = int(self.window_manager.WINDOW_WIDTH * self.window_manager.BORDER_SIDES)

        # Draw border rectangles
        pygame.draw.rect(self.window_manager.screen, Colors.GREY, (0, 0, self.window_manager.WINDOW_WIDTH, top))
        pygame.draw.rect(self.window_manager.screen, Colors.GREY, (0, self.window_manager.WINDOW_HEIGHT - bot, self.window_manager.WINDOW_WIDTH, bot))
        pygame.draw.rect(self.window_manager.screen, Colors.GREY, (0, 0, sides, self.window_manager.WINDOW_HEIGHT))
        pygame.draw.rect(self.window_manager.screen, Colors.GREY, (self.window_manager.WINDOW_WIDTH - sides, 0, sides, self.window_manager.WINDOW_HEIGHT))

    def _draw_game_objects(self, game_objs: ValuesView[GameObj], ingame_time: int) -> None:
        """Draw all visible game objects"""
        for game_obj in game_objs:
            if not game_obj.is_visible:
                continue

            self._draw_game_object(game_obj, ingame_time)

    def _draw_game_object(self, game_obj: GameObj, ingame_time: int) -> None:
        """Draw a single game object"""
        pos = self.window_manager.world_to_screen_coords(game_obj.pos.x, game_obj.pos.y)
        size = int(game_obj.size * self.window_manager.PLAY_HEIGHT)

        # Check if the game object has a sprite
        if game_obj.should_render_sprite:
            self._draw_sprite(game_obj, pos, size)
        else:
            # Fallback to circle drawing
            pygame.draw.circle(self.window_manager.screen, game_obj.color, pos, size)

        # Draw cooldown indicator
        self._draw_cooldown_indicator(game_obj, pos, size, ingame_time)

    def _draw_blinking_game_objects(self, game_objs: ValuesView[GameObj], ingame_time: int) -> None:
        """Draw all visible game objects"""
        for game_obj in game_objs:
            if not game_obj.is_visible:
                continue
            self._draw_blinking_game_object(game_obj, ingame_time)


    def _draw_blinking_game_object(self, game_obj: GameObj, ingame_time: int) -> None:
        """Draws a game object with Slither.io-style flicker, glow image, and cooldown overlay."""
        pos = self.window_manager.world_to_screen_coords(game_obj.pos.x, game_obj.pos.y)
        base_size = int(game_obj.size * self.window_manager.PLAY_HEIGHT)

        # --- Flicker animation (brightness + pulse) ---
        flicker_speed = 6.0  # how fast it pulses
        phase = (game_obj.pos.x * 7 + game_obj.pos.y * 13) % (2 * math.pi)
        time_sec = ingame_time / 1000.0
        flicker = 0.5 + 0.5 * math.sin(time_sec * flicker_speed + phase)
        brightness = 0.7 + 0.3 * flicker  # between 0.7x and 1.0x brightness
        size = int(base_size * (1.0 + 0.05 * flicker))

        # Adjusted color brightness
        r, g, b = game_obj.color
        color = (min(int(r * brightness), 255), min(int(g * brightness), 255), min(int(b * brightness), 255))

        # --- Bobbing animation (hovering left/right, up/down) ---
        bob_amplitude = 0.08 * base_size # Adjust this value to control how much it bobs
        bob_speed_x = 2.0 # How fast it bobs horizontally
        bob_speed_y = 1.5 # How fast it bobs vertically
        # Use different phase offsets for X and Y to create a less linear movement
        bob_offset_x = bob_amplitude * math.sin(time_sec * bob_speed_x + phase)
        bob_offset_y = bob_amplitude * 0.7 * math.sin(time_sec * bob_speed_y + phase + math.pi / 2) # 0.7 makes Y bob less dramatically

        # Apply bobbing offset to the drawing position
        display_pos = (pos[0] + bob_offset_x, pos[1] + bob_offset_y)


        # --- Draw glow using preloaded glow.png ---
        glow_size = int(base_size * 3.2 * (1.0 + 0.05 * flicker))
        if glow_size % 2 != 0:  # ensure even dimensions
            glow_size += 1
        glow = pygame.transform.smoothscale(self.glow_img, (glow_size, glow_size))
        # Tint glow by color
        glow_tinted = glow.copy()
        glow_tinted.fill(color + (0,), special_flags=pygame.BLEND_RGBA_ADD)  # or MULT
        # Manually center to avoid rounding errors
        # Calculate the scaled offset (important to fix offset bug due to improper scaled svg)
        SVG_OFFSET_X = -1
        SVG_OFFSET_Y = -1
        scaled_offset_x = int(SVG_OFFSET_X * (glow_size / self.glow_img.get_width()))
        scaled_offset_y = int(SVG_OFFSET_Y * (glow_size / self.glow_img.get_height()))
        top_left = (
            int(display_pos[0] - glow_size // 2) + scaled_offset_x, # Use display_pos here
            int(display_pos[1] - glow_size // 2) + scaled_offset_y  # Use display_pos here
        )
        self.window_manager.screen.blit(glow_tinted, top_left)

        # Draw main orb
        pygame.draw.circle(self.window_manager.screen, color, display_pos, size) # Use display_pos here

        # --- Draw cooldown overlay LAST (on top of everything) ---
        self._draw_cooldown_indicator(game_obj, display_pos, base_size, ingame_time) # Use display_pos here


    def _draw_sprite(self, game_obj: GameObj, pos: tuple, size: int) -> None:
        """Draw a sprite for the game object"""
        sprite = self.sprite_manager.get_sprite(game_obj.sprite_name)

        # Scale sprite to match the desired size
        sprite_size = size * 2  # Diameter
        scaled_sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size))

        # Center the sprite on the position
        sprite_rect = scaled_sprite.get_rect(center=pos)
        self.window_manager.screen.blit(scaled_sprite, sprite_rect)

    def _draw_cooldown_indicator(self, game_obj: GameObj, pos: tuple, size: int, ingame_time: int) -> None:
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

    @staticmethod
    def _load_glow_effect():
        glow_img = pygame.image.load("assets/images/Food.svg").convert_alpha()
        PADDING = 2  # Workaround for SVG's bounding box being incorrectly cropped
        w, h = glow_img.get_size()
        padded_glow_image = pygame.Surface((w + PADDING * 2, h + PADDING * 2), pygame.SRCALPHA)
        padded_glow_image.blit(glow_img, (PADDING, PADDING))
        return padded_glow_image

    def _draw_animations(self) -> None:
        """Draw all active animations"""
        self.animation_manager.render(self.window_manager.screen, self.window_manager)

    def _draw_fps(self, fps: int) -> None:
        """Draw the FPS counter"""
        fps_text = self.font.render(f"FPS: {fps}", True, Colors.WHITE)
        self.window_manager.screen.blit(fps_text, (10, 10))