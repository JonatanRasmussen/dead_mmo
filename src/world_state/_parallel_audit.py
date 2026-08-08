from typing import Sequence
from src.world_state._event_system import UpcomingEvent, Outcome


class ParallelAudit:
    """Compares legacy (GameObj/Spell) decisions against the new ECS decisions."""

    RAISE_ON_MISMATCH = False
    # Range checks read positions from dead-reckoned movement data, so borderline
    # OUT_OF_RANGE vs SUCCESS disagreements are tolerated (logged as WARN).
    TOLERATE_RANGE_DISAGREEMENT = True

    @staticmethod
    def compare_resolution(u_event: UpcomingEvent, legacy_target: int, legacy_outcome: Outcome,
                           new_target: int, new_outcome: Outcome) -> bool:
        issues = []
        if legacy_target != new_target:
            issues.append(f"target mismatch: OLD={legacy_target} NEW={new_target}")
        if legacy_outcome != new_outcome:
            range_case = Outcome.OUT_OF_RANGE in (legacy_outcome, new_outcome)
            tag = "WARN(range)" if (range_case and ParallelAudit.TOLERATE_RANGE_DISAGREEMENT) else "FAIL"
            issues.append(f"{tag} outcome mismatch: OLD={legacy_outcome} NEW={new_outcome}")
        if not issues:
            return True
        msg = (f"[AUDIT t={u_event.timestamp}] event={u_event.event_id} "
               f"src={u_event.source_id} spell={u_event.spell_id} :: " + " | ".join(issues))
        print(msg)
        if ParallelAudit.RAISE_ON_MISMATCH and "FAIL" in msg:
            raise AssertionError(msg)
        return False

    @staticmethod
    def _key(e: UpcomingEvent) -> tuple:
        # event_id intentionally excluded (independent id streams during hybrid)
        return (e.timestamp, e.source_id, e.spell_id, e.target_id, e.priority,
                e.aura_id, e.is_aoe_targeting, e.is_spell_sequence)

    @staticmethod
    def compare_cascades(parent: UpcomingEvent, legacy: Sequence[UpcomingEvent],
                         new: Sequence[UpcomingEvent]) -> bool:
        old_keys = [ParallelAudit._key(e) for e in legacy]
        new_keys = [ParallelAudit._key(e) for e in new]
        if old_keys == new_keys:
            return True
        print(f"[AUDIT t={parent.timestamp}] cascade mismatch for spell={parent.spell_id} "
              f"src={parent.source_id}\n  OLD={old_keys}\n  NEW={new_keys}")
        if ParallelAudit.RAISE_ON_MISMATCH:
            raise AssertionError("cascade mismatch")
        return False