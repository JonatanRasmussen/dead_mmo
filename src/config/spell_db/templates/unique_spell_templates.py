from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen


class UniqueSpellTemplates:
    @staticmethod
    def empty_spell_template(spell_id: int) -> Spell:
        return Spell(
            spell_id=spell_id,
        )

    @staticmethod
    def targeting(spell_id: int, targeting_flag: SpellFlag) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=targeting_flag | SpellFlag.SELF_CAST
        )