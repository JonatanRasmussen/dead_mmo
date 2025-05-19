from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen


class CombatSpellTemplates:
    @staticmethod
    def instant_damage(spell_id: int, power: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            flags=SpellFlag.DAMAGE | SpellFlag.TRIGGER_GCD,
        )

    @staticmethod
    def instant_heal(spell_id: int, power: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            flags=SpellFlag.HEAL | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def periodic_damage(spell_id: int, aura_effect_id: int, power: float, duration: float, ticks: int) -> Spell:
        return Spell(
            spell_id=spell_id,
            effect_id=aura_effect_id,
            power=power,
            duration=duration,
            ticks=ticks,
            flags=SpellFlag.AURA_APPLY | SpellFlag.DAMAGE  | SpellFlag.TRIGGER_GCD,
        )

    @staticmethod
    def periodic_heal(spell_id: int, aura_effect_id: int, power: float, duration: float, ticks: int) -> Spell:
        return Spell(
            spell_id=spell_id,
            effect_id=aura_effect_id,
            power=power,
            duration=duration,
            ticks=ticks,
            flags=SpellFlag.AURA_APPLY | SpellFlag.HEAL | SpellFlag.SELF_CAST,
        )