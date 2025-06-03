# pylint: disable=E1101
import pygame
import sys
from src.controllers.game_instance import GameInstance
from src.pygame.window_manager import WindowManager
from src.pygame.sprite_manager import SpriteManager
from src.pygame.audio_manager import AudioManager
from src.pygame.animation_manager import AnimationManager
from src.pygame.input_handler import InputHandler
from src.pygame.renderer import Renderer
from src.pygame.fps_manager import FPSManager

class PygameLauncher:
    def __init__(self) -> None:
        # Initialize pygame
        pygame.init()

        # Initialize managers
        self.window_manager = WindowManager()
        self.sprite_manager = SpriteManager()
        self.audio_manager = AudioManager()
        self.animation_manager = AnimationManager()
        self.input_handler = InputHandler()
        self.fps_manager = FPSManager(60)
        self.renderer = Renderer(self.window_manager, self.sprite_manager, self.animation_manager)

        # Initialize game instance
        self.game_instance = GameInstance()

    @staticmethod
    def run_game() -> None:
        """Main entry point to run the game"""
        game = PygameLauncher()

        # Setup game
        setup_spell_id = 300
        game.game_instance.setup_game(setup_spell_id)

        # Preload common assets (optional optimization)
        # game.sprite_manager.preload_sprites(['player', 'enemy', 'projectile'])
        # game.animation_manager.preload_animations(['explosion', 'hit_effect', 'heal_effect'])

        # Run main game loop
        game.main_loop()

        # Cleanup
        pygame.quit()
        sys.exit()

    def main_loop(self) -> None:
        """Main game loop"""
        last_time = pygame.time.get_ticks()

        while self.input_handler.is_running():
            # Calculate delta time
            delta_time, last_time = self.fps_manager.get_delta_time(last_time)

            # Process input
            controls = self.input_handler.process_events()

            # Update game state
            self.game_instance.next_frame(delta_time, controls)

            # Get finalized events from this frame
            finalized_events = self.game_instance.view_all_finalized_events_this_frame

            # Process events for audio and animations
            self.audio_manager.process_events(finalized_events)
            self.animation_manager.process_events(finalized_events)

            # Update animations
            self.animation_manager.update(delta_time)

            # Render frame
            game_objs = self.game_instance.view_all_game_objs_to_draw
            self.renderer.draw_frame(game_objs, self.fps_manager.get_fps(), self.game_instance.ingame_time)

            # Maintain target FPS
            self.fps_manager.tick()