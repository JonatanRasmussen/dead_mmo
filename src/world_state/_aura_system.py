from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, Iterable, ValuesView
from dataclasses import dataclass

from src.settings import Consts
from src.world_state import Behavior
from ._event_log import EventLog
from ._id_gen import IdGen
from ._spell_database import SpellDatabase


@dataclass(slots=True)
class SpellAuraData:
    """Aura-relevant data extracted from a Spell."""
    periodic_spell_id: int = Consts.EMPTY_ID
    duration: int = 0
    ticks: int = 1
    applies_aura: bool = False
    cancels_aura: bool = False


@dataclass(slots=True)
class Aura:
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    aura_id: int = Consts.EMPTY_ID
    source_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID
    origin_spell_id: int = Consts.EMPTY_ID
    periodic_spell_id: int = Consts.EMPTY_ID
    start_time: int = 0
    duration: int = 0
    ticks: int = 1

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.source_id, self.origin_spell_id, self.target_id)

    @property
    def tick_timestamps(self) -> Iterable[int]:
        if self.ticks > 0:
            assert self.duration % self.ticks == 0, \
                f"Non-integer tick interval: duration={self.duration}, ticks={self.ticks}"
            tick_interval = self.duration // self.ticks
            for i in range(1, self.ticks + 1):
                yield self.start_time + i * tick_interval

    def is_expired(self, current_time: int) -> bool:
        return current_time > self.start_time + self.duration

    def ticks_remaining(self, current_time: int) -> int:
        return sum(1 for t in self.tick_timestamps if t > current_time)


class AuraSystem:
    """Owns aura runtime state AND the per-spell aura templates."""

    def __init__(self, spell_database: SpellDatabase) -> None:
        self._spell_data: Dict[int, SpellAuraData] = self._build(spell_database)
        self._auras: SortedDict = SortedDict()
        self._aura_id_mappings: dict[int, tuple[int, int, int]] = {}
        self._aura_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

    @staticmethod
    def _build(spell_database: SpellDatabase) -> Dict[int, SpellAuraData]:
        data: Dict[int, SpellAuraData] = {}
        for spell in spell_database.get_all_spells():
            data[spell.spell_id] = SpellAuraData(
                periodic_spell_id=spell.effect_id,
                duration=spell.duration,
                ticks=spell.ticks,
                applies_aura=bool(spell.flags & Behavior.AURA_APPLY),
                cancels_aura=bool(spell.flags & Behavior.AURA_CANCEL),
            )
        return data

    # ---- spell template queries ----------------------------------
    def applies_aura(self, spell_id: int) -> bool:
        data = self._spell_data.get(spell_id)
        return bool(data and data.applies_aura)

    def cancels_aura(self, spell_id: int) -> bool:
        data = self._spell_data.get(spell_id)
        return bool(data and data.cancels_aura)

    # ---- runtime -------------------------------------------------
    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.values()

    def aura_exists(self, aura_id: int) -> bool:
        return aura_id in self._aura_id_mappings

    def get_aura_by_id(self, aura_id: int) -> Aura:
        assert aura_id in self._aura_id_mappings, f"Aura with ID {aura_id} does not exist."
        return self.get_aura_by_key(*self._aura_id_mappings[aura_id])

    def get_aura_by_key(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        key = (source_id, spell_id, target_id)
        assert key in self._auras, f"Aura with key {key} does not exist."
        return self._auras[key]

    def add_aura(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        template = self._spell_data[spell_id]
        new_aura_id = self._aura_id_gen.generate_new_id()
        aura = Aura(
            aura_id=new_aura_id,
            source_id=source_id,
            origin_spell_id=spell_id,
            periodic_spell_id=template.periodic_spell_id,
            target_id=target_id,
            start_time=timestamp,
            duration=template.duration,
            ticks=template.ticks,
        )
        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_new_aura_creation(aura.key)
        if aura.key in self._auras:
            self.remove_aura(source_id, spell_id, target_id)
        self._auras[aura.key] = aura
        self._aura_id_mappings[new_aura_id] = aura.key
        return new_aura_id

    def remove_aura(self, source_id: int, spell_id: int, target_id: int) -> None:
        key = (source_id, spell_id, target_id)
        assert key in self._auras, f"Failed to remove aura: key {key} does not exist."
        aura = self._auras[key]
        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_aura_deletion(aura.key)
        del self._auras[key]
        del self._aura_id_mappings[aura.aura_id]

    def try_remove_aura(self, source_id: int, spell_id: int, target_id: int) -> bool:
        """Non-asserting variant (legacy code assumed the aura exists)."""
        key = (source_id, spell_id, target_id)
        if key not in self._auras:
            return False
        self.remove_aura(source_id, spell_id, target_id)
        return True