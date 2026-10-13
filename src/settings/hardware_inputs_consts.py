from .consts import Consts
from .game_input import GameInput

class HardwareInputConsts:
    KEYBOARD_KEYDOWN_ABILITY_1 = "BUILTIN_KEYBOARD_KEYDOWN_1"
    KEYBOARD_KEYDOWN_ABILITY_2 = "BUILTIN_KEYBOARD_KEYDOWN_2"
    KEYBOARD_KEYDOWN_ABILITY_3 = "BUILTIN_KEYBOARD_KEYDOWN_3"
    KEYBOARD_KEYDOWN_ABILITY_4 = "BUILTIN_KEYBOARD_KEYDOWN_4"

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
    def get_spell_names_for_player_inputs(player_id: int, player_inputs: list[str]) -> list[str]:
        spell_names = []
        if player_id != Consts.EMPTY_OBJ_ID:
            for player_input in player_inputs:
                match player_input:
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_1: spell_names.append("molten_blast_aoe")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_2: spell_names.append("shadow_blast_buttonpress")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_3: spell_names.append("input_ability_3")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ABILITY_4: spell_names.append("input_ability_4")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: spell_names.append("tab_target_spell")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: spell_names.append("input_startmove_up")
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: spell_names.append("input_stopmove_up")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: spell_names.append("input_startmove_left")
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: spell_names.append("input_stopmove_left")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: spell_names.append("input_startmove_down")
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: spell_names.append("input_stopmove_down")
                    case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: spell_names.append("input_startmove_right")
                    case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: spell_names.append("input_stopmove_right")
        return spell_names