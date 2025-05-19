from typing import Dict, List, Tuple, ValuesView
import heapq

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObjStatus, GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import EventOutcome, CombatEvent

class SpellValidation:
    @staticmethod
    def decide_outcome(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> EventOutcome:
        if source_obj.status == GameObjStatus.DESPAWNED:
            return EventOutcome.FAILED_SOURCE_HAS_DESPAWNED
        if target_obj.status == GameObjStatus.DESPAWNED:
            return EventOutcome.FAILED_TARGET_HAS_DESPAWNED
        if not SpellValidation.is_within_range(source_obj, spell, target_obj):
            return EventOutcome.FAILED_NOT_WITHIN_RANGE
        return EventOutcome.SUCCESS

    @staticmethod
    def is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.flags & SpellFlag.HAS_RANGE_LIMIT:
            return True
        return (source_obj.x - target_obj.x) ** 2 + (source_obj.y - target_obj.y) ** 2 <= spell.range_limit ** 2
