from typing import Iterable, Union, Mapping
from dataclasses import dataclass, field
import json

from src.settings import Consts
from .controls import Controls, KeyPresses


# Calculate once when the module is imported as a performance optimization.
LOADOUT_KEY_TO_INDEX_MAP: dict[KeyPresses, int] = {
    key: key.value.bit_length() - 1 for key in KeyPresses if key != KeyPresses.NONE
}

@dataclass(slots=True)
class Loadout:
    """Used by GameObjs to map controls inputs to spell events"""

    spawn_timestamp: int = Consts.EMPTY_TIMESTAMP
    spell_ids: list[int] = field(default_factory=lambda: [Consts.EMPTY_ID] * len(LOADOUT_KEY_TO_INDEX_MAP))
    ability_cds: list[int] = field(default_factory=lambda: [Consts.EMPTY_TIMESTAMP] * len(LOADOUT_KEY_TO_INDEX_MAP))
    gcd_start: int = -1_000

    @classmethod
    def deserialize(cls, data: str) -> 'Loadout':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            spawn_timestamp=d["ts"],
            spell_ids=d["ids"],
            ability_cds=d["cds"],
            gcd_start=d["gcd"]
        )
    def serialize(self) -> str:
        return json.dumps({
            "ts": self.spawn_timestamp,
            "ids": self.spell_ids,
            "cds": self.ability_cds,
            "gcd": self.gcd_start
        })

    @classmethod
    def create_from_bindings(cls, bindings: dict[KeyPresses, int]) -> 'Loadout':
        """Creates and configures a Loadout from a dictionary of bindings."""
        loadout = cls()
        for key, spell_id in bindings.items():
            loadout.bind_spell(key, spell_id)
        return loadout

    def bind_spell(self, key_presses: KeyPresses, spell_id: int) -> 'Loadout':
        """Binds each keypress in key_presses to spell_id"""
        for flag in LOADOUT_KEY_TO_INDEX_MAP:
            if flag in key_presses:
                index = LOADOUT_KEY_TO_INDEX_MAP[flag]
                self.spell_ids[index] = spell_id
        return self  # Returns self to allow chaining

    def convert_controls_to_spell_ids(self, controls: Controls, obj_id: int) -> Iterable[int]:
        """Fast conversion using direct list indexing."""
        assert not controls.is_empty, f"Controls for {obj_id} is empty."
        for key_flag in LOADOUT_KEY_TO_INDEX_MAP:
            if key_flag in controls.key_presses:
                idx = LOADOUT_KEY_TO_INDEX_MAP[key_flag]
                spell_id = self.spell_ids[idx]
                assert Consts.is_valid_id(spell_id), f"Invalid spell ID for {obj_id}: {key_flag.name}_id"
                yield spell_id