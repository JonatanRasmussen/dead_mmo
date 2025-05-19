from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.collections.unique_spell_collection import UniqueSpellCollection


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
    def damaging_aura(spell_id: int, aura_effect_id: int, power: float, duration: float, ticks: int) -> Spell:
        return Spell(
            spell_id=spell_id,
            effect_id=aura_effect_id,
            power=power,
            duration=duration,
            ticks=ticks,
            flags=SpellFlag.AURA_APPLY | SpellFlag.DAMAGE | SpellFlag.SELF_CAST | SpellFlag.TRIGGER_GCD,
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

    @staticmethod
    def hitbox_tick(spell_id: int, power: float, range_limit: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            range_limit=range_limit,
            flags=SpellFlag.DAMAGE | SpellFlag.HAS_RANGE_LIMIT | SpellFlag.IGNORE_TARGET,
        )

    @staticmethod
    def single_tick_hitbox(spell_id: int, power: float, range_limit: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            range_limit=range_limit,
            flags=SpellFlag.DAMAGE | SpellFlag.HAS_RANGE_LIMIT | SpellFlag.IGNORE_TARGET,
            spell_sequence=(
                UniqueSpellCollection.despawn_self().spell_id,
            )
        )
