from src.settings import Consts
from src.settings import HardwareInputConsts
from ._yaml_spell_loader import YamlSpellLoader, SelfcastValidation, TriggerEffect


class SpellHandler:
    def __init__(self, spell_loader: YamlSpellLoader) -> None:
        self.spell_loader = spell_loader
        self.spell_database = self.spell_loader.spell_database

    @classmethod
    def initialize_with_loaded_spells(cls, system_effect_types: set[str], system_validation_types: set[str]) -> "SpellHandler":
        spell_loader = YamlSpellLoader()
        valid_effect_types = system_effect_types | {t.value for t in TriggerEffect}
        valid_validation_types = system_validation_types | {s.value for s in SelfcastValidation}
        spell_loader.validate_types(valid_effect_types, valid_validation_types)
        return SpellHandler(spell_loader)

    def get_asset_name(self, asset_id: float) -> str:
        return self.spell_loader.get_asset_name(asset_id)

    def get_effects(self, spell_id: int) -> dict[str, float]:
        spell = self.spell_database.get(spell_id)
        return spell.effects if spell else {}

    def get_validations(self, spell_id: int) -> dict[str, float]:
        spell = self.spell_database.get(spell_id)
        return spell.validations if spell else {}

    def get_cascades(self, spell_id: int) -> list[int]:
        spell = self.spell_database.get(spell_id)
        return spell.cascade if spell is not None else []

    def is_spell_spawning_as_child(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and TriggerEffect.SPAWN_AS_CHILD in spell.effects

    def is_spell_sent_as_signal(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and TriggerEffect.SEND_AS_SIGNAL in spell.effects

    def get_spell_delay(self, spell_id: int) -> int:
        delay = 0
        spell = self.spell_database.get(spell_id)
        if spell is not None and TriggerEffect.FIRE_WITH_DELAY in spell.effects:
            delay += round(spell.effects[TriggerEffect.FIRE_WITH_DELAY])
        return delay

    def is_spell_selfcast(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and SelfcastValidation.IS_SELFCAST in spell.validations

    def get_timeline_for_spell(self, spell_id: int) -> dict[int, list[int]]:
        spell = self.spell_database.get(spell_id)
        return spell.timeline if spell is not None else {}

    def get_signal_spell_id(self, spell_id: int) -> int:
        spell = self.spell_database.get(spell_id)
        return spell.signal_spell_id if spell is not None else Consts.EMPTY_SPELL_ID

    def get_aoe_spell_id(self, spell_id: int) -> int:
        spell = self.spell_database.get(spell_id)
        return spell.aoe_spell_id if spell is not None else Consts.EMPTY_SPELL_ID

    def get_spells_for_player_inputs(self, player_id: int, player_inputs: list[str]) -> list[int]:
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