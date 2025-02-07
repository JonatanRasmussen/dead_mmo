# pylint: disable=E1101
import pygame
import sys
from typing import List, Tuple
from src.model.manager import GameManager, GameObj, Color

class PygameLauncher:
    def __init__(self) -> None:
        self.WINDOW_WIDTH = 1920
        self.WINDOW_HEIGHT = 1080

        self.BORDER_TOP = 0.1
        self.BORDER_BOT = 0.2
        self.BORDER_SIDES = 0.05
        self.PLAY_RATIO = 1/1

        self.screen = None
        self.running = True
        self.game_manager = GameManager()

    @staticmethod
    def run_game() -> None:
        # setup pygame
        game = PygameLauncher()
        pygame.init()
        pygame.display.set_caption("placeholder")
        game.screen = pygame.display.set_mode((game.WINDOW_WIDTH, game.WINDOW_HEIGHT))
        game.calculate_play_area() # Calculate play area dimensions and adjusted borders

        # setup game manager
        game.game_manager.setup_game(10)

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

        # Abilities
        ability_1 = keys[pygame.K_1]
        ability_2 = keys[pygame.K_2]
        ability_3 = keys[pygame.K_3]
        ability_4 = keys[pygame.K_4]

        # Process events for quitting
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False

        # Update game state
        self.game_manager.process_server_tick(
            delta_time,
            move_up, move_left, move_down, move_right,
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
        game_objs: List[GameObj] = self.game_manager.get_all_game_objs_to_draw()
        for game_obj in game_objs:
            # Convert from unit coordinates (0-1) to screen coordinates
            screen_x = self.BORDER_SIDES * self.WINDOW_WIDTH + game_obj.x * self.PLAY_WIDTH
            screen_y = self.BORDER_TOP * self.WINDOW_HEIGHT + (1 - game_obj.y) * self.PLAY_HEIGHT
            pos = (int(screen_x), int(screen_y))

            # Using a default size and color since they're not provided in the tuple
            size = int(game_obj.get_size() * self.PLAY_HEIGHT)  # Default size
            pygame.draw.circle(self.screen, Color.RED, pos, size)

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