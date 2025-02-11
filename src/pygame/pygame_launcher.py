# pylint: disable=E1101
import math
import pygame
import sys
from typing import List, Tuple, Optional, ValuesView
from src.model.models import GameObj
from src.config.color import Color
from src.handlers.handler import GameInstance

class PygameLauncher:
    def __init__(self) -> None:
        self.WINDOW_WIDTH: int = 1920
        self.WINDOW_HEIGHT: int = 1080

        self.PLAY_WIDTH: float = 0.0
        self.PLAY_HEIGHT: float = 0.0
        self.movement_adjustment_x: float = 0.0
        self.movement_adjustment_y: float = 0.0

        self.BORDER_TOP: float = 0.1
        self.BORDER_BOT: float = 0.2
        self.BORDER_SIDES: float = 0.05
        self.PLAY_RATIO: float = 1/1

        self.screen: pygame.Surface = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        self.running: bool = True
        self.game_manager: GameInstance = GameInstance()

    @staticmethod
    def run_game() -> None:
        # setup pygame
        game = PygameLauncher()
        pygame.init()
        pygame.display.set_caption("placeholder")
        game.calculate_play_area() # Calculate play area dimensions and adjusted borders

        # setup game manager
        game.game_manager.setup_game(300)

        # run game loop
        last_time = pygame.time.get_ticks()
        while game.running:
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_time) / 1000.0  # Convert to seconds
            last_time = current_time

            game.process_game_tick(delta_time)
            game.draw_screen()
            pygame.time.Clock().tick(60)
        pygame.quit()
        sys.exit()

    def process_game_tick(self, delta_time: float) -> None:
        keys = pygame.key.get_pressed()

        # Movement
        move_up = keys[pygame.K_w]
        move_left = keys[pygame.K_a]
        move_down = keys[pygame.K_s]
        move_right = keys[pygame.K_d]

        # Targeting
        next_target = False

        # Abilities
        ability_1 = False
        ability_2 = False
        ability_3 = False
        ability_4 = False

        for event in pygame.event.get():
            # Process events for quitting
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            # Ability key down presses
            elif event.type == pygame.KEYDOWN:
                next_target = event.key == pygame.K_TAB
                ability_1 = event.key == pygame.K_1
                ability_2 = event.key == pygame.K_2
                ability_3 = event.key == pygame.K_3
                ability_4 = event.key == pygame.K_4

        # Update game state
        self.game_manager.process_server_tick(
            delta_time,
            move_up, move_left, move_down, move_right, next_target,
            ability_1, ability_2, ability_3, ability_4
        )

    def draw_screen(self) -> None:
        self.screen.fill(Color.BLACK)
        # Draw borders
        top = int(self.WINDOW_HEIGHT * self.BORDER_TOP)
        bot = int(self.WINDOW_HEIGHT * self.BORDER_BOT)
        sides = int(self.WINDOW_WIDTH * self.BORDER_SIDES)
        pygame.draw.rect(self.screen, Color.GREY, (0, 0, self.WINDOW_WIDTH, top))
        pygame.draw.rect(self.screen, Color.GREY, (0, self.WINDOW_HEIGHT - bot, self.WINDOW_WIDTH, bot))
        pygame.draw.rect(self.screen, Color.GREY, (0, 0, sides, self.WINDOW_HEIGHT))
        pygame.draw.rect(self.screen, Color.GREY, (self.WINDOW_WIDTH - sides, 0, sides, self.WINDOW_HEIGHT))

        # Draw game objects
        game_objs: ValuesView[GameObj] = self.game_manager.get_all_game_objs_to_draw()
        for game_obj in game_objs:
            # Convert from unit coordinates (0-1) to screen coordinates
            screen_x = self.BORDER_SIDES * self.WINDOW_WIDTH + game_obj.x * self.PLAY_WIDTH
            screen_y = self.BORDER_TOP * self.WINDOW_HEIGHT + (1 - game_obj.y) * self.PLAY_HEIGHT
            pos = (int(screen_x), int(screen_y))

            # Using a default size and color since they're not provided in the tuple
            size = int(game_obj.size * self.PLAY_HEIGHT)  # Default size
            pygame.draw.circle(self.screen, game_obj.color, pos, size)

            """ To implement later: Each game object has a .gcd_progress attribute with
                a value between 0.0 (empty) and 1.0 (full). Instead of circles, I want a
                radial cooldown indicator that fills clockwise from 12 o'clock. """
            # Draw the cooldown indicator
            progress = game_obj.gcd_progress
            if progress < 1.0:  # Only draw if not fully cooled down
                # Calculate the angle for the progress (0 to 360 degrees)
                angle = progress * 360

                # Create a surface for the cooldown overlay
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

                # Draw the darkened overlay
                pygame.draw.circle(surf, (0, 0, 0, 128), (size, size), size)  # Semi-transparent black

                if angle > 0:  # Draw the revealed portion
                    # Convert angle to radians and adjust starting position
                    start_angle = -270  # Start from 12 o'clock position
                    end_angle = start_angle + angle

                    # Draw the pie shape to reveal the underlying circle
                    pygame.draw.arc(surf, (0, 0, 0, 0), (0, 0, size * 2, size * 2),
                                math.radians(start_angle), math.radians(end_angle), size)

                # Blit the overlay onto the main screen
                self.screen.blit(surf, (pos[0] - size, pos[1] - size))

        pygame.display.flip()

    def calculate_play_area(self) -> None:
        # Calculate maximum possible play area dimensions considering minimum borders
        max_play_width = self.WINDOW_WIDTH * (1 - 2 * self.BORDER_SIDES)
        max_play_height = self.WINDOW_HEIGHT * (1 - self.BORDER_TOP - self.BORDER_BOT)

        # Calculate actual play area dimensions maintaining ratio
        if max_play_width/max_play_height > self.PLAY_RATIO:
            # Too wide, adjust width
            self.PLAY_HEIGHT = max_play_height
            self.PLAY_WIDTH = self.PLAY_HEIGHT * self.PLAY_RATIO
            # Center horizontally with extra border
            extra_width = max_play_width - self.PLAY_WIDTH
            self.BORDER_SIDES = self.BORDER_SIDES + (extra_width / (2 * self.WINDOW_WIDTH))
        else:
            # Too tall, adjust height
            self.PLAY_WIDTH = max_play_width
            self.PLAY_HEIGHT = self.PLAY_WIDTH / self.PLAY_RATIO
            # Center vertically with extra border
            extra_height = max_play_height - self.PLAY_HEIGHT
            extra_top = extra_height / 2
            self.BORDER_TOP = self.BORDER_TOP + (extra_top / self.WINDOW_HEIGHT)
            self.BORDER_BOT = self.BORDER_BOT + (extra_top / self.WINDOW_HEIGHT)

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