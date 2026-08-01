from .hardware_inputs_consts import HardwareInputConsts

class LevelSetupConsts:

    TEST_SETUP_SPELL_IDS: list[int] = [300]
    SCRIPTED_PLAYER_INPUT_FOR_TESTING: dict[int, list[str]] = {
        200: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP],
        300: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT ],
        400: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT , HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP],
        500: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN, HardwareInputConsts.KEYBOARD_KEYDOWN_4],
        600: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN , HardwareInputConsts.KEYBOARD_KEYDOWN_TAB],
        700: [HardwareInputConsts.KEYBOARD_KEYDOWN_4],
        1800: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN , HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT , HardwareInputConsts.KEYBOARD_KEYDOWN_3],
        3800: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN , HardwareInputConsts.KEYBOARD_KEYDOWN_1],
        5300: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT , HardwareInputConsts.KEYBOARD_KEYDOWN_2],
    }