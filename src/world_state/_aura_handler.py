from sortedcontainers import SortedDict  # type: ignore
from typing import Iterable, ValuesView

from src.settings import Consts
from src.models.events import Aura, UpcomingEvent
from ._event_log import EventLog
from ._id_gen import IdGen
from src.models.data import Spell


class AuraHandler:

    def __init__(self) -> None:
        self._auras: SortedDict = SortedDict()
        self._aura_id_mappings: dict[int, tuple[int, int, int]] = {}
        self._aura_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.values()

    def aura_exists(self, u_event: UpcomingEvent) -> bool:
        #key = self._create_aura_key(u_event.source_id, u_event.aura_origin_spell_id, u_event.target_id)
        #if key not in self._auras:
        #    return False
        #aura = self.get_aura_by_key(*key)
        #return aura.start_time == u_event.aura_start_time
        return u_event.aura_id in self._aura_id_mappings

    def get_aura_by_id(self, aura_id: int) -> Aura:
        assert aura_id in self._aura_id_mappings, f"Aura with ID {aura_id} does not exist."
        key = self._aura_id_mappings[aura_id]
        return self.get_aura_by_key(*key)

    def get_aura_by_key(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        key = self._create_aura_key(source_id, spell_id, target_id)
        assert key in self._auras, f"Aura with ID {key} does not exist."
        return self._auras[key]

    def add_aura(self, timestamp: int, source_id: int, spell: Spell, target_id: int) -> int:
        new_aura_id = self._aura_id_gen.generate_new_id()
        aura = Aura(
            aura_id=new_aura_id,
            source_id=source_id,
            origin_spell_id=spell.spell_id,
            periodic_spell_id=spell.effect_id,
            target_id=target_id,
            start_time=timestamp,
            duration=spell.duration,
            ticks=spell.ticks,
        )

        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_new_aura_creation(aura)

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
            EventLog.summarize_aura_deletion(aura)

        # Remove from both structures
        del self._auras[key]
        del self._aura_id_mappings[aura.aura_id]

    @staticmethod
    def _create_aura_key(source_id: int, spell_id: int, target_id: int) -> tuple[int, int, int]:
        return (source_id, spell_id, target_id)