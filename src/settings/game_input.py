from enum import Enum
from .consts import Consts

class GameInput(int, Enum):
    KEYBOARD_KEYDOWN_ABILITY_1 = -1
    KEYBOARD_KEYDOWN_ABILITY_2 = -2
    KEYBOARD_KEYDOWN_ABILITY_3 = -3
    KEYBOARD_KEYDOWN_ABILITY_4 = -4

    KEYBOARD_KEYDOWN_TAB = -5

    KEYBOARD_KEYDOWN_ARROW_UP = -6
    KEYBOARD_KEYUP_ARROW_UP = -7

    KEYBOARD_KEYDOWN_ARROW_LEFT = -8
    KEYBOARD_KEYUP_ARROW_LEFT = -9

    KEYBOARD_KEYDOWN_ARROW_DOWN = -10
    KEYBOARD_KEYUP_ARROW_DOWN = -11

    KEYBOARD_KEYDOWN_ARROW_RIGHT = -12
    KEYBOARD_KEYUP_ARROW_RIGHT = -13

    @staticmethod
    def create_input_spell_name(input_id: int) -> str:
        assert input_id < 0, f"Error: input_id {input_id} should be negative to avoid spell_id collisions."
        assert input_id in [game_input.value for game_input in GameInput], f"Error: input_id {input_id} does not match a known GameInput"
        return f"{Consts.INPUT_SPELL_NAME}_{input_id * -1}"