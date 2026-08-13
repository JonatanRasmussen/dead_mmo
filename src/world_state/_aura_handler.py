from sortedcontainers import SortedDict  # type: ignore
from typing import Iterable, ValuesView, Dict
from dataclasses import dataclass

from src.settings import Consts
from ._event_log import EventLog
from ._id_gen import IdGen
from ._spell_database import SpellDatabase


@dataclass(slots=True)
class Aura:
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    aura_id: int = Consts.EMPTY_ID  # unique id for each aura
    source_id: int = Consts.EMPTY_ID  # game_obj source
    target_id: int = Consts.EMPTY_ID  # game_obj target
    origin_spell_id: int = Consts.EMPTY_ID  # spell that applied aura
    periodic_spell_id: int = Consts.EMPTY_ID  # spell to be cast each tick
    start_time: int = 0
    duration: int = 0
    ticks: int = 1

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.source_id, self.origin_spell_id, self.target_id)

    @property
    def tick_timestamps(self) -> Iterable[int]:
        """Yield timestamps for all ticks occuring during the aura's lifetime. """
        if self.ticks > 0:
            assert self.duration % self.ticks == 0, f"Non-integer tick interval: duration={self.duration}, ticks={self.ticks}"
            tick_interval = self.duration // self.ticks
            for i in range(1, self.ticks + 1):
                timestamp = self.start_time + i * tick_interval
                assert isinstance(timestamp, int), f"Non-int tick timestamp: {timestamp}"
                yield timestamp

    def is_expired(self, current_time: int) -> bool:
        end_time = self.start_time + self.duration
        return current_time > end_time

    def ticks_remaining(self, current_time: int) -> int:
        return sum(1 for t in self.tick_timestamps if t > current_time)



@dataclass(slots=True)
class SpellAuraData:
    effect_id: int = Consts.EMPTY_ID
    duration: int = 0
    ticks: int = 1


class AuraHandler:

    def __init__(self, spell_database: SpellDatabase) -> None:
        self._auras: SortedDict = SortedDict()
        self._spell_data_dct: dict[int, SpellAuraData] = self._create_initialized_spell_data_dct(spell_database)
        self._aura_id_mappings: dict[int, tuple[int, int, int]] = {}
        self._aura_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> dict[int, SpellAuraData]:
        spell_data_dct = {}
        for spell in spell_database.get_all_spells():
            spell_data_dct[spell.spell_id] = SpellAuraData(
            effect_id=spell.effect_id,
            duration=spell.duration,
            ticks=spell.ticks,
        )
        return spell_data_dct

    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.values()

    def aura_exists(self, aura_id: int) -> bool:
        #key = self._create_aura_key(u_event.source_id, u_event.aura_origin_spell_id, u_event.target_id)
        #if key not in self._auras:
        #    return False
        #aura = self.get_aura_by_key(*key)
        #return aura.start_time == u_event.aura_start_time
        return aura_id in self._aura_id_mappings

    def get_aura_by_id(self, aura_id: int) -> Aura:
        assert aura_id in self._aura_id_mappings, f"Aura with ID {aura_id} does not exist."
        key = self._aura_id_mappings[aura_id]
        return self.get_aura_by_key(*key)

    def get_aura_by_key(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        key = self._create_aura_key(source_id, spell_id, target_id)
        assert key in self._auras, f"Aura with ID {key} does not exist."
        return self._auras[key]

    def add_aura(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        new_aura_id = self._aura_id_gen.generate_new_id()
        spell_data = self._spell_data_dct[spell_id]
        aura = Aura(
            aura_id=new_aura_id,
            source_id=source_id,
            origin_spell_id=spell_id,
            periodic_spell_id=spell_data.effect_id,
            target_id=target_id,
            start_time=timestamp,
            duration=spell_data.duration,
            ticks=spell_data.ticks,
        )

        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_new_aura_creation(aura.key)

        key = aura.key

        # Handle aura already existing
        if key in self._auras:
            self.remove_aura(source_id, aura.origin_spell_id, target_id)

        self._auras[key] = aura
        self._aura_id_mappings[aura.aura_id] = key

        return new_aura_id

    def remove_aura(self, source_id: int, spell_id: int, target_id: int) -> None:
        key = self._create_aura_key(source_id, spell_id, target_id)
        assert key in self._auras, f"Failed to remove aura: Aura ID {key} does not exist."

        aura = self._auras[key]

        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_aura_deletion(aura.key)

        # Remove from both structures
        del self._auras[key]
        del self._aura_id_mappings[aura.aura_id]

    @staticmethod
    def _create_aura_key(source_id: int, spell_id: int, target_id: int) -> tuple[int, int, int]:
        return (source_id, spell_id, target_id)