from src.models.spell import SpellFlag, Spell, GameObjStatus, GameObj
from src.models.event import EventOutcome

class SpellValidation:
    @staticmethod
    def decide_outcome(timestamp: float, source_obj: GameObj, spell: Spell, target_obj: GameObj) -> EventOutcome:
        if target_obj.status == GameObjStatus.DESPAWNED:
            return EventOutcome.FAILED_TARGET_HAS_DESPAWNED
        if source_obj.status == GameObjStatus.DESPAWNED:
            return EventOutcome.FAILED_SOURCE_HAS_DESPAWNED
        if not SpellValidation.is_within_range(source_obj, spell, target_obj):
            return EventOutcome.FAILED_NOT_WITHIN_RANGE
        if not SpellValidation.gcd_is_available(timestamp, source_obj, spell):
            return EventOutcome.FAILED_GCD_NOT_READY
        return EventOutcome.SUCCESS

    @staticmethod
    def is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.flags & SpellFlag.HAS_RANGE_LIMIT:
            return True
        return (source_obj.x - target_obj.x) ** 2 + (source_obj.y - target_obj.y) ** 2 <= spell.range_limit ** 2

    @staticmethod
    def gcd_is_available(timestamp: float, source_obj: GameObj, spell: Spell) -> bool:
        if not spell.flags & SpellFlag.TRIGGER_GCD:
            return True
        return source_obj.get_gcd_progress(timestamp) >= 1.0