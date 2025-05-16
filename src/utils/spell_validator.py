from typing import Dict, List, Tuple, ValuesView
import heapq

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import EventOutcome, CombatEvent
from src.config.spell_db import SpellDatabase


class SpellValidator:
    @staticmethod
    def decide_outcome(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> EventOutcome:
        # not implemented
        assert source_obj.obj_id + spell.spell_id + target_obj.obj_id > 0, "just a placeholder"
        return EventOutcome.SUCCESS
