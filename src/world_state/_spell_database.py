from typing import Any, Iterable, Type

from src.world_state import Spell
from src.world_state._spell_factories import SpellFactory
from src.world_state._spell_configs import BasicMovement, BasicTargeting, NpcTargetDummy, NpcBoss, NpcHealingPowerup, NpcLandmine, SpecWarlock, ZoneTestGround

class SpellDatabase:
    def __init__(self) -> None:
        self.spells_loaded_into_memory: dict[int, Spell] = SpellDatabase._load_spells_into_memory()

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells_loaded_into_memory, f"Spell with ID {spell_id} not found."
        return self.spells_loaded_into_memory.get(spell_id, Spell())

    def get_all_spells(self) -> Iterable[Spell]:
        """Helper to yield all spells for system initializations."""
        return self.spells_loaded_into_memory.values()

    @staticmethod
    def _load_spells_into_memory() -> dict[int, Spell]:
        spells_to_load: list[SpellFactory] = []
        spells_to_load += SpellDatabase._load_collection(BasicMovement)
        spells_to_load += SpellDatabase._load_collection(BasicTargeting)
        spells_to_load += SpellDatabase._load_collection(NpcBoss)
        spells_to_load += SpellDatabase._load_collection(NpcHealingPowerup)
        spells_to_load += SpellDatabase._load_collection(NpcLandmine)
        spells_to_load += SpellDatabase._load_collection(NpcTargetDummy)
        spells_to_load += SpellDatabase._load_collection(SpecWarlock)
        spells_to_load += SpellDatabase._load_collection(ZoneTestGround)
        spells_loaded_into_memory: dict[int, Spell] = {}
        for spell_factory in spells_to_load:
            spell = spell_factory.build()
            assert spell.spell_id not in spells_loaded_into_memory, f"Spell with ID {spell.spell_id} already exists."
            spells_loaded_into_memory[spell.spell_id] = spell
        return spells_loaded_into_memory

    @staticmethod
    def _load_collection(class_with_methods: Type[Any]) -> list[Any]:
        static_methods = [name for name, attr in class_with_methods.__dict__.items() if isinstance(attr, staticmethod)]
        return [getattr(class_with_methods, method)() for method in static_methods]
