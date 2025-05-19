from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.combat_spell_templates import CombatSpellTemplates


class CombatSpellCollection:
    @staticmethod
    def fireblast() -> Spell:
        return CombatSpellTemplates.instant_damage(
            spell_id=114,
            power=3.0,
        )

    @staticmethod
    def small_heal() -> Spell:
        return CombatSpellTemplates.instant_heal(
            spell_id=112,
            power=8.0,
        )

    @staticmethod
    def healing_aura() -> Spell:
        return CombatSpellTemplates.periodic_heal(
            spell_id=113,
            aura_effect_id=CombatSpellCollection.small_heal().spell_id,
            power=20.0,
            duration=6.0,
            ticks=10,
        )

