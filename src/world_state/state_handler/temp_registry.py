from src.settings import HardwareInputConsts, AudioFiles, SpriteFiles

class InputRegistry:
    """ Maps hardware input strings directly to Spell IDs """
    BINDINGS = {
        HardwareInputConsts.KEYBOARD_KEYDOWN_1: 128,
        HardwareInputConsts.KEYBOARD_KEYDOWN_2: 113,
        HardwareInputConsts.KEYBOARD_KEYDOWN_3: 171,
        HardwareInputConsts.KEYBOARD_KEYDOWN_4: 124,
        HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: 15,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: 91,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: 92,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: 181,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: 182,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: 271,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: 272,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: 1,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: 2,
    }

    @classmethod
    def get_spells_for_inputs(cls, player_inputs: list[str]) -> list[int]:
        """ Returns a list of Spell IDs corresponding to the active inputs. """
        return [cls.BINDINGS[i] for i in player_inputs if i in cls.BINDINGS]


class AssetRegistry:
    """ Maps Spell IDs to Audio and Sprite file names """
    SPELL_AUDIO_MAP = {
        171: AudioFiles.REJUVENATION_APPLY,
        111: AudioFiles.SHADOW_BOLT_HIT,
        911: AudioFiles.SHADOW_BOLT_BUILD,
        116: AudioFiles.SHADOW_BOLT_HIT,
        41: AudioFiles.SHADOW_BOLT_CAST,
    }

    SPELL_SPRITE_MAP = {
        42: SpriteFiles.PORO_PLAYER,
    }

    SPELL_COLOUR_MAP = {
        1042: (0, 0, 255),
        2042: (0, 255, 0),
        3042: (255, 0, 0),
    }


    @classmethod
    def get_audio(cls, spell_id: int) -> str:
        return cls.SPELL_AUDIO_MAP.get(spell_id, "")

    @classmethod
    def get_sprite(cls, spell_id: int) -> str:
        return cls.SPELL_SPRITE_MAP.get(spell_id, "")