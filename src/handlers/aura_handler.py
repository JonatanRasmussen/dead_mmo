from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.models.spell import SpellFlag, Spell
from src.models.aura import Aura
from src.handlers.event_log import EventLog


class AuraHandler:

    def __init__(self) -> None:
        self._auras: SortedDict[Tuple[int, int, int], Aura] = SortedDict()

    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.values()

    def add_aura(self, timestamp: float, source_id: int, spell: Spell, target_id: int) -> None:
        aura = Aura.create_from_spell(timestamp, source_id, spell, target_id)
        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_new_aura_creation(aura)
        key: Tuple[int, int, int] = aura.aura_id
        assert key not in self._auras, f"Aura with (source, spell, target) = ({key}) already exists."
        self._auras[key] = aura

    def get_aura(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        key: Tuple[int, int, int] = (source_id, spell_id, target_id)
        assert key in self._auras, f"Aura with ID {key} does not exist."
        return self._auras.get(key, Aura())

    def get_obj_auras(self, obj_id: int) -> List[Aura]:
        return [aura for aura in self._auras.values() if aura.target_id == obj_id]