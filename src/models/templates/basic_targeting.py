from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, Behavior, Targeting, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates


class BasicTargeting:
    @staticmethod
    def targetswap_to_next_tab_target() -> SpellFactory:
        return (
            SpellFactory(15)
            .cast_on_next_tab_target()
            .update_current_target()
        )
    @staticmethod
    def targetswap_to_parent() -> SpellFactory:
        return (
            SpellFactory(16)
            .cast_on_parent()
            .update_current_target()
        )
    @staticmethod
    def targetswap_to_parents_current_target() -> SpellFactory:
        return (
            SpellFactory(17)
            .cast_on_parent()
            .add_flag(Behavior.TARGET_OF_TARGET)
            .update_current_target()
        )