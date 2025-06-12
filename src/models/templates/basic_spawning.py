from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates


class BasicSpawning:
    @staticmethod
    def empty_spell() -> SpellFactory:
        return (
            SpellFactory(Consts.EMPTY_ID)
        )

    @staticmethod
    def despawn_self() -> SpellFactory:
        return (
            SpellFactory(33)
            .cast_on_self()
            .add_flag(SpellFlag.DESPAWN_SELF)
        )
