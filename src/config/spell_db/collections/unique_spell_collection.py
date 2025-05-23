from src.models.spell import SpellFlag, Spell, IdGen
from src.config.spell_db.templates.spell_templates import SpellTemplates


class UniqueSpellCollection:
    @staticmethod
    def empty_spell() -> Spell:
        return SpellTemplates.empty_spell_template(
            spell_id=IdGen.EMPTY_ID
        )

    @staticmethod
    def despawn_self() -> Spell:
        return SpellTemplates.apply_flag_to_self(
            spell_id=33,
            spell_flag=SpellFlag.DESPAWN_SELF
        )

    @staticmethod
    def tab_target() -> Spell:
        return SpellTemplates.apply_flag_to_self(
            spell_id=15,
            spell_flag=SpellFlag.TAB_TARGET
        )
