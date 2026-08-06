import pygame
from src.settings import HardwareInputConsts

class InputHandler:

    def __init__(self):
        self.running = True

    def fetch_player_input(self) -> list[str]:
        """Process pygame events and return a list of input constants"""
        inputs: list[str] = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event, inputs)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event, inputs)

        return inputs

    def _handle_keyup(self, event: pygame.event.Event, inputs: list[str]) -> None:
        if event.key == pygame.K_w:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP)
        elif event.key == pygame.K_a:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT)
        elif event.key == pygame.K_s:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN)
        elif event.key == pygame.K_d:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT)

    def _handle_keydown(self, event: pygame.event.Event, inputs: list[str]) -> None:
        if event.key == pygame.K_w:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP)
        elif event.key == pygame.K_a:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT)
        elif event.key == pygame.K_s:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN)
        elif event.key == pygame.K_d:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT)
        elif event.key == pygame.K_TAB:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_TAB)
        elif event.key == pygame.K_1:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_1)
        elif event.key == pygame.K_2:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_2)
        elif event.key == pygame.K_3:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_3)
        elif event.key == pygame.K_4:
            inputs.append(HardwareInputConsts.KEYBOARD_KEYDOWN_4)

    def is_running(self) -> bool:
        return self.running