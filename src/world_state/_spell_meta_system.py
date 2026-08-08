from dataclasses import dataclass
from enum import IntFlag, auto
from typing import Dict

from src.settings import Consts
from src.world_state import Behavior, Targeting
from ._spell_database import SpellDatabase


class MetaBehavior(IntFlag):
    """Non-combat, non-movement spell flags (targeting/validation/spawn/aura/cascade)."""
    NONE = 0
    AOE = auto()
    TRIGGER_GCD = auto()
    DENY_IF_CASTING = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    AURA_APPLY = auto()
    AURA_CANCEL = auto()

    @classmethod
    def from_behavior(cls, behavior: Behavior) -> "MetaBehavior":
        result = cls.NONE
        for flag in cls:
            if flag is not cls.NONE and flag.name is not None and behavior & getattr(Behavior, flag.name):
                result |= flag
        return result


@dataclass(slots=True)
class SpellMetaData:
    spell_id: int
    targeting: Targeting
    range_limit: float
    cast_time: int
    spell_sequence: tuple[int, ...]
    flags: MetaBehavior
    spawns_obj: bool
    has_cascading_events: bool


class SpellMetaSystem:
    """
    Owns everything about a spell that is neither combat stats, movement, controls nor cosmetics:
    targeting mode, range/cast validation, spawn intent, aura intent and cascading sequences.
    """

    def __init__(self, spell_database: SpellDatabase) -> None:
        self._meta: Dict[int, SpellMetaData] = self._build(spell_database)

    @staticmethod
    def _build(spell_database: SpellDatabase) -> Dict[int, SpellMetaData]:
        meta: Dict[int, SpellMetaData] = {}
        for spell in spell_database.get_all_spells():
            flags = MetaBehavior.from_behavior(spell.flags)
            sequence = tuple(spell.spell_sequence) if spell.spell_sequence else ()
            spawns_obj = spell.spawned_obj is not None
            has_cascade = bool(flags & MetaBehavior.AOE or flags & MetaBehavior.AURA_APPLY or spawns_obj or sequence)
            meta[spell.spell_id] = SpellMetaData(
                spell_id=spell.spell_id,
                targeting=spell.targeting,
                range_limit=spell.range_limit,
                cast_time=spell.cast_time,
                spell_sequence=sequence,
                flags=flags,
                spawns_obj=spawns_obj,
                has_cascading_events=has_cascade,
            )
        return meta

    # ---- queries -------------------------------------------------
    def get(self, spell_id: int) -> SpellMetaData:
        assert spell_id in self._meta, f"Spell {spell_id} has no metadata."
        return self._meta[spell_id]

    def get_targeting(self, spell_id: int) -> Targeting:
        return self.get(spell_id).targeting

    def get_range_limit(self, spell_id: int) -> float:
        return self.get(spell_id).range_limit

    def get_spell_sequence(self, spell_id: int) -> tuple[int, ...]:
        return self.get(spell_id).spell_sequence

    def is_area_of_effect(self, spell_id: int) -> bool:
        return bool(self.get(spell_id).flags & MetaBehavior.AOE)

    def triggers_gcd(self, spell_id: int) -> bool:
        return bool(self.get(spell_id).flags & MetaBehavior.TRIGGER_GCD)

    def spawns_obj(self, spell_id: int) -> bool:
        return self.get(spell_id).spawns_obj

    def despawns_source(self, spell_id: int) -> bool:
        return bool(self.get(spell_id).flags & MetaBehavior.DESPAWN_SELF)

    def spawns_boss(self, spell_id: int) -> bool:
        return bool(self.get(spell_id).flags & MetaBehavior.SPAWN_BOSS)

    def spawns_player(self, spell_id: int) -> bool:
        return bool(self.get(spell_id).flags & MetaBehavior.SPAWN_PLAYER)

    def has_cascading_events(self, spell_id: int) -> bool:
        return self.get(spell_id).has_cascading_events