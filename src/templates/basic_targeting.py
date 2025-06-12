from src.config import AudioFiles, Colors, Consts
from src.models import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.handlers.spell_factory import SpellFactory, SpellTemplates


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
            .cast_on_target_of_target()
            .update_current_target()
        )