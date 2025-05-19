from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.unique_spell_templates import UniqueSpellTemplates


class UniqueSpellCollection:
    @staticmethod
    def empty_spell() -> Spell:
        return UniqueSpellTemplates.empty_spell_template(
            spell_id=IdGen.EMPTY_ID
        )

    @staticmethod
    def despawn_self() -> Spell:
        return UniqueSpellTemplates.self_apply_flag_template(
            spell_id=33,
            spell_flag=SpellFlag.DESPAWN
        )

    @staticmethod
    def tab_target() -> Spell:
        return UniqueSpellTemplates.self_apply_flag_template(
            spell_id=15,
            spell_flag=SpellFlag.TAB_TARGET
        )
