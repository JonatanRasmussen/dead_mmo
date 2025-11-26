# pylint: disable=E1101
import pygame
import sys
from src.models.managers.combat_instance import CombatInstance
from .window_manager import WindowManager
from .sprite_manager import SpriteManager
from .audio_manager import AudioManager
from .animation_manager import AnimationManager
from .input_handler import InputHandler
from .renderer import Renderer
from .fps_manager import FPSManager

class PygameLauncher:
    def __init__(self) -> None:
        pygame.init()  # Initialize pygame

        # Initialize managers
        self.window_manager = WindowManager()
        self.sprite_manager = SpriteManager()
        self.audio_manager = AudioManager()
        self.animation_manager = AnimationManager()
        self.input_handler = InputHandler()
        self.fps_manager = FPSManager(165)
        self.renderer = Renderer(self.window_manager, self.sprite_manager, self.animation_manager)

        # Initialize game instance
        self.game_instance = CombatInstance(setup_spell_ids=[300])

    @staticmethod
    def run_game() -> None:
        """Main entry point to run the game"""
        game = PygameLauncher()

        # Preload common assets (optional optimization)
        # game.sprite_manager.preload_sprites(['player', 'enemy', 'projectile'])
        # game.animation_manager.preload_animations(['explosion', 'hit_effect', 'heal_effect'])
        game.main_loop()  # Run main game loop

        pygame.quit()  # Cleanup
        sys.exit()

    def main_loop(self) -> None:
        """Main game loop"""
        last_time = pygame.time.get_ticks()
        while self.input_handler.is_running():
            delta_time, last_time = self.fps_manager.get_delta_time(last_time)
            controls = self.input_handler.fetch_player_input()
            delta_time_in_ms = self.game_instance.convert_delta_time_to_int_in_ms(delta_time)
            self.game_instance.process_next_frame(delta_time_in_ms, controls)
            finalized_events = self.game_instance.view_all_events_this_frame
            self.audio_manager.process_events(finalized_events)
            self.animation_manager.process_events(finalized_events)
            self.animation_manager.update(delta_time)
            game_objs = self.game_instance.view_all_game_objs_to_draw
            self.renderer.draw_frame(game_objs, self.fps_manager.get_fps(), self.game_instance.ingame_time)
            self.fps_manager.tick()  # Maintain target FPS