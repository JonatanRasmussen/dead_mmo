from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, Iterable, ValuesView

from src.config import Consts
from src.models.components import Aura, UpcomingEvent, FinalizedEvent
from src.models.services import EventLog, IdGen


class AuraHandler:

    def __init__(self) -> None:
        self._auras: SortedDict[Tuple[int, int, int], Aura] = SortedDict()
        self._aura_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.values()

    def aura_exists(self, u_event: UpcomingEvent) -> bool:
        key = self.create_aura_key(u_event.source_id, u_event.aura_origin_spell_id, u_event.target_id)
        if key not in self._auras:
            return False
        aura = self.get_aura(key[0], key[1], key[2])
        return aura.aura_id == u_event.aura_id

    def get_aura(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        key = self.create_aura_key(source_id, spell_id, target_id)
        assert key in self._auras, f"Aura with ID {key} does not exist."
        return self._auras.get(key, Aura())

    def get_obj_auras(self, obj_id: int) -> Iterable[Aura]:
        start_key = self.create_aura_key(obj_id, Consts.MIN_ID, Consts.MIN_ID)
        end_key = self.create_aura_key(obj_id, Consts.MAX_ID, Consts.MAX_ID)
        yield from (self._auras[key] for key in self._auras.irange(start_key, end_key))

    def handle_aura(self, f_event: FinalizedEvent) -> None:
        if f_event.spell.has_aura_cancel:
            self.remove_aura(f_event.source_id, f_event.spell.external_spell, f_event.target_id)
        if f_event.spell.has_aura_apply:
            self.add_aura(f_event)

    def add_aura(self, f_event: FinalizedEvent) -> None:
        aura = Aura(
            aura_id = self._aura_id_gen.generate_new_id(),
            source_id=f_event.source_id,
            origin_spell_id=f_event.spell.spell_id,
            periodic_spell_id=f_event.spell.external_spell,
            target_id=f_event.target_id,
            start_time=f_event.timestamp,
            duration=f_event.spell.duration,
            ticks=f_event.spell.ticks,
        )
        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_new_aura_creation(aura)

        # Handle aura already existing
        self.try_remove_aura(aura.source_id, aura.origin_spell_id, aura.target_id)

        key: Tuple[int, int, int] = aura.get_key_for_aura
        assert key not in self._auras, f"Aura with (source, spell, target) = ({key}) already exists."
        self._auras[key] = aura

    def try_remove_aura(self, source_id: int, spell_id: int, target_id: int) -> None:
        key = self.create_aura_key(source_id, spell_id, target_id)
        if key in self._auras:
            self.remove_aura(source_id, spell_id, target_id)

    def remove_aura(self, source_id: int, spell_id: int, target_id: int) -> None:
        key = self.create_aura_key(source_id, spell_id, target_id)
        assert key in self._auras, f"Failed to remove aura: Aura ID {key} does not exist."
        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_aura_deletion(self.get_aura(source_id, spell_id, target_id))
        del self._auras[key]

    @staticmethod
    def create_aura_key(source_id: int, spell_id: int, target_id: int) -> Tuple[int, int, int]:
        return (source_id, spell_id, target_id)