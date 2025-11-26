# input_handler.py (Updated)
import pygame
from src.models.components.controls import Controls, KeyPresses

from src.frontend_client.pygame_renderer.pygame_renderer import IInputReader

class InputHandler(IInputReader):
    def __init__(self):
        self.running = True

    def fetch_player_input(self) -> str:
        """Process pygame events and return a Controls object"""
        controls = Controls()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event, controls)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event, controls)

        return controls.serialize()

    def _handle_keyup(self, event: pygame.event.Event, controls: Controls) -> None:
        """Handle key release events"""
        if event.key == pygame.K_w:
            controls.key_presses |= KeyPresses.STOP_MOVE_UP
        elif event.key == pygame.K_a:
            controls.key_presses |= KeyPresses.STOP_MOVE_LEFT
        elif event.key == pygame.K_s:
            controls.key_presses |= KeyPresses.STOP_MOVE_DOWN
        elif event.key == pygame.K_d:
            controls.key_presses |= KeyPresses.STOP_MOVE_RIGHT

    def _handle_keydown(self, event: pygame.event.Event, controls: Controls) -> None:
        """Handle key press events"""
        if event.key == pygame.K_w:
            controls.key_presses |= KeyPresses.START_MOVE_UP
        elif event.key == pygame.K_a:
            controls.key_presses |= KeyPresses.START_MOVE_LEFT
        elif event.key == pygame.K_s:
            controls.key_presses |= KeyPresses.START_MOVE_DOWN
        elif event.key == pygame.K_d:
            controls.key_presses |= KeyPresses.START_MOVE_RIGHT
        elif event.key == pygame.K_TAB:
            controls.key_presses |= KeyPresses.SWAP_TARGET
        elif event.key == pygame.K_1:
            controls.key_presses |= KeyPresses.ABILITY_1
        elif event.key == pygame.K_2:
            controls.key_presses |= KeyPresses.ABILITY_2
        elif event.key == pygame.K_3:
            controls.key_presses |= KeyPresses.ABILITY_3
        elif event.key == pygame.K_4:
            controls.key_presses |= KeyPresses.ABILITY_4

    def is_running(self) -> bool:
        """Check if the game should continue running"""
        return self.running