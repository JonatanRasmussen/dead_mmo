import pygame
from src.models.controls import Controls

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
                controls = self._handle_keyup(event, controls)
            elif event.type == pygame.KEYDOWN:
                controls = self._handle_keydown(event, controls)

        return controls

    def _handle_keyup(self, event: pygame.event.Event, controls: Controls) -> Controls:
        """Handle key release events"""
        if event.key == pygame.K_w:
            return controls._replace(stop_move_up=True)
        elif event.key == pygame.K_a:
            return controls._replace(stop_move_left=True)
        elif event.key == pygame.K_s:
            return controls._replace(stop_move_down=True)
        elif event.key == pygame.K_d:
            return controls._replace(stop_move_right=True)
        return controls

    def _handle_keydown(self, event: pygame.event.Event, controls: Controls) -> Controls:
        """Handle key press events"""
        if event.key == pygame.K_w:
            return controls._replace(start_move_up=True)
        elif event.key == pygame.K_a:
            return controls._replace(start_move_left=True)
        elif event.key == pygame.K_s:
            return controls._replace(start_move_down=True)
        elif event.key == pygame.K_d:
            return controls._replace(start_move_right=True)
        elif event.key == pygame.K_TAB:
            return controls._replace(next_target=True)
        elif event.key == pygame.K_1:
            return controls._replace(ability_1=True)
        elif event.key == pygame.K_2:
            return controls._replace(ability_2=True)
        elif event.key == pygame.K_3:
            return controls._replace(ability_3=True)
        elif event.key == pygame.K_4:
            return controls._replace(ability_4=True)
        return controls

    def is_running(self) -> bool:
        """Check if the game should continue running"""
        return self.running