from .hardware_inputs_consts import HardwareInputConsts

class LevelSetupConsts:

    OMEGA_SETUP_SPELL_NAMES: list[str] = ["init_bravo_boss", "init_player"]
    BRAVO_SETUP_SPELL_NAMES: list[str] = ["bravo_setup"]  # Previously 6767
    TEST_SETUP_SPELL_NAMES: list[str] = ["test_setup"]    # Previously 300

    SCRIPTED_PLAYER_INPUT_FOR_TESTING: dict[int, list[str]] = {
        200: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP],
        300: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT ],
        400: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT , HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP],
        500: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN, HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_4],
        600: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN , HardwareInputConsts.KEYBOARD_KEYDOWN_TAB],
        700: [HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_4],
        1800: [HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN , HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT , HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_3],
        3800: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN , HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_1],
        5300: [HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT , HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_2],
    }