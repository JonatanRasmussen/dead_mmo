from .consts import Consts

class HardwareInputConsts:

    KEYBOARD_KEYDOWN_1 = "BUILTIN_KEYBOARD_KEYDOWN_1"
    KEYBOARD_KEYDOWN_2 = "BUILTIN_KEYBOARD_KEYDOWN_2"
    KEYBOARD_KEYDOWN_3 = "BUILTIN_KEYBOARD_KEYDOWN_3"
    KEYBOARD_KEYDOWN_4 = "BUILTIN_KEYBOARD_KEYDOWN_4"

    KEYBOARD_KEYDOWN_TAB = "BUILTIN_KEYBOARD_KEYDOWN_TAB"

    KEYBOARD_KEYDOWN_ARROW_UP = "BUILTIN_KEYBOARD_KEYDOWN_ARROW_UP"
    KEYBOARD_KEYUP_ARROW_UP = "BUILTIN_KEYBOARD_KEYUP_ARROW_UP"

    KEYBOARD_KEYDOWN_ARROW_LEFT  = "BUILTIN_KEYBOARD_KEYDOWN_ARROW_LEFT"
    KEYBOARD_KEYUP_ARROW_LEFT  = "BUILTIN_KEYBOARD_KEYUP_ARROW_LEFT"

    KEYBOARD_KEYDOWN_ARROW_DOWN  = "BUILTIN_KEYBOARD_KEYDOWN_ARROW_DOWN"
    KEYBOARD_KEYUP_ARROW_DOWN  = "BUILTIN_KEYBOARD_KEYUP_ARROW_DOWN"

    KEYBOARD_KEYDOWN_ARROW_RIGHT  = "BUILTIN_KEYBOARD_KEYDOWN_ARROW_RIGHT"
    KEYBOARD_KEYUP_ARROW_RIGHT  = "BUILTIN_KEYBOARD_KEYUP_ARROW_RIGHT"

    @staticmethod
    def get_spells_for_player_inputs(player_id: int, player_inputs: list[str]) -> list[int]:
        spell_ids = []
        if player_id != Consts.EMPTY_OBJ_ID:
            for player_input in player_inputs:
                match player_input:
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_1: spell_ids.append(128)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_2: spell_ids.append(911)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_3: spell_ids.append(170)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_4: spell_ids.append(1440)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: spell_ids.append(15)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: spell_ids.append(91)
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: spell_ids.append(92)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: spell_ids.append(181)
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: spell_ids.append(182)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: spell_ids.append(271)
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: spell_ids.append(272)
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: spell_ids.append(1)
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: spell_ids.append(2)
        return spell_ids