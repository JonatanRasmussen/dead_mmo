from typing import Any, List, Dict, Type

from src.models.spell import Spell
from src.config.spell_db.collections.combat_spell_collection import CombatSpellCollection
from src.config.spell_db.collections.instance_spell_collection import InstanceSpellCollection
from src.config.spell_db.collections.movement_spell_collection import MovementSpellCollection
from src.config.spell_db.collections.spawn_spell_collection import SpawnSpellCollection
from src.config.spell_db.collections.unique_spell_collection import UniqueSpellCollection

class SpellDatabase:
    def __init__(self) -> None:
        self.spells_loaded_into_memory: Dict[int, Spell] = SpellDatabase.load_spells_into_memory()

    @staticmethod
    def load_spells_into_memory() -> Dict[int, Spell]:
        spells_to_load: List[Spell] = []
        spells_to_load += SpellDatabase._load_collection(UniqueSpellCollection)
        spells_to_load += SpellDatabase._load_collection(MovementSpellCollection)
        spells_to_load += SpellDatabase._load_collection(CombatSpellCollection)
        spells_to_load += SpellDatabase._load_collection(SpawnSpellCollection)
        spells_to_load += SpellDatabase._load_collection(InstanceSpellCollection)
        spells_loaded_into_memory: Dict[int, Spell] = {}
        for spell in spells_to_load:
            assert spell.spell_id not in spells_loaded_into_memory, f"Spell with ID {spell.spell_id} already exists."
            spells_loaded_into_memory[spell.spell_id] = spell
        return spells_loaded_into_memory

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells_loaded_into_memory, f"Spell with ID {spell_id} not found."
        return self.spells_loaded_into_memory.get(spell_id, Spell())

    @staticmethod
    def _load_collection(class_with_methods: Type[Any]) -> List[Any]:
        static_methods = [name for name, attr in class_with_methods.__dict__.items() if isinstance(attr, staticmethod)]
        return [getattr(class_with_methods, method)() for method in static_methods]
