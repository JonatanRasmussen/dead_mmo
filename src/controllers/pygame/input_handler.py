import pygame
from src.models.components import Controls

class InputHandler:
    def __init__(self):
        self.running = True

    def process_events(self) -> Controls:
        """Process pygame events and return a Controls object"""
        controls = Controls()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event, controls)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event, controls)

        return controls

    def _handle_keyup(self, event: pygame.event.Event, controls: Controls) -> None:
        """Handle key release events"""
        if event.key == pygame.K_w:
            controls.stop_move_up = True
        elif event.key == pygame.K_a:
            controls.stop_move_left = True
        elif event.key == pygame.K_s:
            controls.stop_move_down = True
        elif event.key == pygame.K_d:
            controls.stop_move_right = True

    def _handle_keydown(self, event: pygame.event.Event, controls: Controls) -> None:
        """Handle key press events"""
        if event.key == pygame.K_w:
            controls.start_move_up = True
        elif event.key == pygame.K_a:
            controls.start_move_left = True
        elif event.key == pygame.K_s:
            controls.start_move_down = True
        elif event.key == pygame.K_d:
            controls.start_move_right = True
        elif event.key == pygame.K_TAB:
            controls.swap_target = True
        elif event.key == pygame.K_1:
            controls.ability_1 = True
        elif event.key == pygame.K_2:
            controls.ability_2 = True
        elif event.key == pygame.K_3:
            controls.ability_3 = True
        elif event.key == pygame.K_4:
            controls.ability_4 = True

    def is_running(self) -> bool:
        """Check if the game should continue running"""
        return self.running