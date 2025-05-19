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
    def tab_target() -> Spell:
        return UniqueSpellTemplates.targeting(
            spell_id=15,
            targeting_flag=SpellFlag.TAB_TARGET
        )
