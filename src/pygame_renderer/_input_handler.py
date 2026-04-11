# input_handler.py (Updated)
import pygame
from src.models.components.controls import KeyPresses

class InputHandler:
    def __init__(self):
        self.running = True

    def fetch_player_input(self) -> KeyPresses:
        """Process pygame events and return a KeyPresses object"""
        key_presses: KeyPresses = KeyPresses.NONE

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.KEYUP:
                key_presses = self._handle_keyup(event, key_presses)
            elif event.type == pygame.KEYDOWN:
                key_presses = self._handle_keydown(event, key_presses)

        return key_presses

    def _handle_keyup(self, event: pygame.event.Event, key_presses: KeyPresses) -> KeyPresses:
        """Handle key release events"""
        if event.key == pygame.K_w:
            key_presses |= KeyPresses.STOP_MOVE_UP
        elif event.key == pygame.K_a:
            key_presses |= KeyPresses.STOP_MOVE_LEFT
        elif event.key == pygame.K_s:
            key_presses |= KeyPresses.STOP_MOVE_DOWN
        elif event.key == pygame.K_d:
            key_presses |= KeyPresses.STOP_MOVE_RIGHT
        return key_presses

    def _handle_keydown(self, event: pygame.event.Event, key_presses: KeyPresses) -> KeyPresses:
        """Handle key press events"""
        if event.key == pygame.K_w:
            key_presses |= KeyPresses.START_MOVE_UP
        elif event.key == pygame.K_a:
            key_presses |= KeyPresses.START_MOVE_LEFT
        elif event.key == pygame.K_s:
            key_presses |= KeyPresses.START_MOVE_DOWN
        elif event.key == pygame.K_d:
            key_presses |= KeyPresses.START_MOVE_RIGHT
        elif event.key == pygame.K_TAB:
            key_presses |= KeyPresses.SWAP_TARGET
        elif event.key == pygame.K_1:
            key_presses |= KeyPresses.ABILITY_1
        elif event.key == pygame.K_2:
            key_presses |= KeyPresses.ABILITY_2
        elif event.key == pygame.K_3:
            key_presses |= KeyPresses.ABILITY_3
        elif event.key == pygame.K_4:
            key_presses |= KeyPresses.ABILITY_4
        return key_presses

    def is_running(self) -> bool:
        """Check if the game should continue running"""
        return self.running