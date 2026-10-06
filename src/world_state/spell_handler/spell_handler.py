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

    def get_spell_id(self, spell_name: str) -> int:
        return self.spell_loader.get_spell_id(spell_name)

    def get_spell_name(self, spell_id: int) -> str:
        spell = self.spell_database.get(spell_id)
        return spell.name if spell else "unknown_spell"

    def get_asset_name(self, asset_id: float) -> str:
        return self.spell_loader.get_asset_name(asset_id)

    def get_effects(self, spell_id: int) -> dict[str, float]:
        spell = self.spell_database.get(spell_id)
        return spell.effects if spell else {}

    def get_validations(self, spell_id: int) -> dict[str, float]:
        spell = self.spell_database.get(spell_id)
        return spell.validations if spell else {}

    def is_spell_spawning_as_child(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and TriggerEffect.SPAWN_AS_CHILD in spell.effects

    def is_spell_targeting_self(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and bool(spell.validations.get(Consts.IS_TARGETING_SELF, False))

    def is_spell_targeting_destination(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and bool(spell.validations.get(Consts.IS_TARGETING_DESTINATION, False))

    def get_timeline_for_spell(self, spell_id: int) -> dict[int, list[int]]:
        spell = self.spell_database.get(spell_id)
        return spell.timeline if spell is not None else {}