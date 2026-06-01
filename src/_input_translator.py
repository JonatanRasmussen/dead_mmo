from src.models.components.key_presses import KeyPresses


from typing import Iterable
from .models.components import KeyPresses
from src.consts import HardwareInputConsts

class InputTranslator:

    _HARDWARE_TO_KEYPRESSES: dict[str, KeyPresses] = {
        HardwareInputConsts.KEYBOARD_KEYDOWN_1: KeyPresses.ABILITY_1,
        HardwareInputConsts.KEYBOARD_KEYDOWN_2: KeyPresses.ABILITY_2,
        HardwareInputConsts.KEYBOARD_KEYDOWN_3: KeyPresses.ABILITY_3,
        HardwareInputConsts.KEYBOARD_KEYDOWN_4: KeyPresses.ABILITY_4,

        HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: KeyPresses.SWAP_TARGET,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: KeyPresses.START_MOVE_UP,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: KeyPresses.STOP_MOVE_UP,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: KeyPresses.START_MOVE_LEFT,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: KeyPresses.STOP_MOVE_LEFT,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: KeyPresses.START_MOVE_DOWN,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: KeyPresses.STOP_MOVE_DOWN,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: KeyPresses.START_MOVE_RIGHT,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: KeyPresses.STOP_MOVE_RIGHT,
    }
    @staticmethod
    def translate_to_keypresses(inputs: Iterable[str]) -> KeyPresses:
        result = KeyPresses.NONE

        for input_const in inputs:
            try:
                result |= InputTranslator._HARDWARE_TO_KEYPRESSES[input_const]
            except KeyError as exc:
                raise ValueError(f"Unknown input const: {input_const}") from exc

        return result