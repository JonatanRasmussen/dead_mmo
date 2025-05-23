from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.spell_templates import SpellTemplates


class CombatSpellCollection:
    @staticmethod
    def fireblast() -> Spell:
        return SpellTemplates.instant_damage(
            spell_id=111,
            power=13.0,
        )

    @staticmethod
    def small_heal() -> Spell:
        return SpellTemplates.instant_heal(
            spell_id=112,
            power=8.0,
        )

    @staticmethod
    def healing_aura() -> Spell:
        return SpellTemplates.periodic_heal(
            spell_id=113,
            aura_effect_id=CombatSpellCollection.small_heal().spell_id,
            power=20.0,
            duration=6.0,
            ticks=10,
        )

    @staticmethod
    def pointy_ball_tick() -> Spell:
        return SpellTemplates.hitbox_tick(
            spell_id=114,
            power=0.5,
            range_limit=0.2
        )

    @staticmethod
    def short_range_hurtbox() -> Spell:
        return SpellTemplates.damaging_aura(
            spell_id=115,
            aura_effect_id=CombatSpellCollection.pointy_ball_tick().spell_id,
            power=10.0,
            duration=20.0,
            ticks=200,
        )

    @staticmethod
    def proximity_trigger() -> Spell:
        return SpellTemplates.damaging_aura(
            spell_id=116,
            aura_effect_id=CombatSpellCollection.pointy_ball_tick().spell_id,
            power=10.0,
            duration=20.0,
            ticks=200,
        )

    @staticmethod
    def landmine_explosion() -> Spell:
        return SpellTemplates.single_tick_hitbox(
            spell_id=117,
            power=90.0,
            range_limit=0.1
        )

    @staticmethod
    def landmine_aura() -> Spell:
        return SpellTemplates.damaging_aura(
            spell_id=118,
            aura_effect_id=CombatSpellCollection.landmine_explosion().spell_id,
            power=5.0,
            duration=20.0,
            ticks=200,
        )