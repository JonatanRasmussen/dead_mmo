from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen


class MovementSpellTemplates:
    @staticmethod
    def step_movement(spell_id: int, direction: SpellFlag) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=direction | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST
        )
    @staticmethod
    def begin_movement(spell_id: int, aura_effect_id: int) -> Spell:
        return Spell(
            spell_id=spell_id,
            effect_id=aura_effect_id,
            duration=60.0,
            ticks=60*250,
            flags=SpellFlag.AURA_APPLY | SpellFlag.SELF_CAST,
        )
    @staticmethod
    def cancel_movement(spell_id: int, aura_effect_id: int) -> Spell:
        return Spell(
            spell_id=spell_id,
            effect_id=aura_effect_id,
            flags=SpellFlag.AURA_CANCEL | SpellFlag.SELF_CAST,
        )
