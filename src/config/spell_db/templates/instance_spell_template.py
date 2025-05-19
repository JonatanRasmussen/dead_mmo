from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen


class InstanceSpellTemplates:
    @staticmethod
    def instance_setup(spell_id: int, spell_sequence: Optional[Tuple[int, ...]]) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.IS_SETUP,
            spell_sequence=spell_sequence,
        )