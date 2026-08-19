from typing import Iterable
from ._spell_data_configs import LegacySpellConfig
from ._spell_data import SpellData

from ._casting_system import CastingSystem
from ._health_system import HealthSystem
from ._movement_system import MovementSystem
from ._targeting_system import TargetingSystem
from ._vfx_and_sfx_system import VfxAndSfxSystem


class SpellDatabase:
    def __init__(self) -> None:
        self.spells_loaded_into_memory: dict[int, SpellData] = self._load_spells_into_memory()

    def get_spell(self, spell_id: int) -> SpellData:
        assert spell_id in self.spells_loaded_into_memory, f"Spell with ID {spell_id} not found."
        return self.spells_loaded_into_memory[spell_id]

    def get_all_spells(self) -> Iterable[SpellData]:
        """Yields all configured NewSpell instances."""
        return self.spells_loaded_into_memory.values()

    # --- System Factories ---

    def create_casting_system(self) -> CastingSystem:
        spell_data_dct = {
            spell_id: spell.to_casting_data()
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return CastingSystem(spell_data_dct)

    def create_health_system(self) -> HealthSystem:
        spell_data_dct = {
            spell_id: spell.to_health_data()
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return HealthSystem(spell_data_dct)

    def create_movement_system(self) -> MovementSystem:
        spell_data_dct = {
            spell_id: spell.to_movement_data()
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return MovementSystem(spell_data_dct)

    def create_targeting_system(self) -> TargetingSystem:
        spell_data_dct = {
            spell_id: spell.to_targeting_data()
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return TargetingSystem(spell_data_dct)

    def create_vfx_and_sfx_system(self) -> VfxAndSfxSystem:
        spell_data_dct = {
            spell_id: spell.to_vfx_data()
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return VfxAndSfxSystem(spell_data_dct)

    # --- Internal Config Loader ---

    @staticmethod
    def _load_spells_into_memory() -> dict[int, SpellData]:
        spells_loaded_into_memory: dict[int, SpellData] = {}

        # Load exactly what is explicitly written in the config file
        for spell in LegacySpellConfig.get_all_spells():
            assert spell.spell_id not in spells_loaded_into_memory, f"Spell with ID {spell.spell_id} already exists."
            spells_loaded_into_memory[spell.spell_id] = spell

        return spells_loaded_into_memory