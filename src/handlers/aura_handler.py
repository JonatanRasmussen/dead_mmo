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

    def get_aura(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        key: Tuple[int, int, int] = (source_id, spell_id, target_id)
        assert key in self._auras, f"Aura with ID {key} does not exist."
        return self._auras.get(key, Aura())

    def get_obj_auras(self, obj_id: int) -> List[Aura]:
        return [aura for aura in self._auras.values() if aura.target_id == obj_id]

    def handle_aura(self, timestamp: float, source_id: int, spell: Spell, target_id: int) -> None:
        if spell.has_aura_cancel: # Try cancel existing aura before applying new one
            self.remove_obj_aura(target_id, spell.effect_id)
        if spell.has_aura_apply:
            self.add_aura(timestamp, source_id, spell, target_id)

    def add_aura(self, timestamp: float, source_id: int, spell: Spell, target_id: int) -> None:
        aura = Aura.create_from_spell(timestamp, source_id, spell, target_id)
        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_new_aura_creation(aura)
        key: Tuple[int, int, int] = aura.aura_id
        assert key not in self._auras, f"Aura with (source, spell, target) = ({key}) already exists."
        self._auras[key] = aura

    def try_remove_obj_aura(self, obj_id: int, spell_id: int) -> None:
        key: Tuple[int, int, int] = (obj_id, spell_id, obj_id)
        if key in self._auras:
            self.remove_obj_aura(obj_id, spell_id)

    def remove_obj_aura(self, obj_id: int, spell_id: int) -> None:
        key: Tuple[int, int, int] = (obj_id, spell_id, obj_id)
        assert key in self._auras, f"Failed to remove aura: Aura ID {key} does not exist."
        if EventLog.DEBUG_PRINT_AURA_UPDATES:
            EventLog.summarize_aura_deletion(self.get_aura(obj_id, spell_id, obj_id))
        del self._auras[key]