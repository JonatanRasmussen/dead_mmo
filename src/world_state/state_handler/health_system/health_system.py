import math
from dataclasses import dataclass
from typing import Dict

@dataclass(slots=True)
class ObjHealthData:
    hp: float = 0.0
    spell_modifier: float = 1.0

class HealthSystem:
    def __init__(self) -> None:
        self._data_dct: Dict[int, ObjHealthData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self._data_dct[obj_id] = ObjHealthData()

    def spawn_game_obj(self, obj_id: int) -> None:
        assert obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[obj_id] = ObjHealthData()

    def remove_game_obj(self, obj_id: int) -> None:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        self._data_dct.pop(obj_id, None)

    def get_data(self, obj_id: int) -> ObjHealthData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    # ---- State Lookups ----

    def get_hp(self, obj_id: int) -> float:
        return self.get_data(obj_id).hp

    def get_size(self, obj_id: int) -> float:
        obj_hp = self.get_data(obj_id).hp
        return 0.01 + math.sqrt(0.0001 * abs(obj_hp))

    def validate_event(self) -> str:
        #Implemented for parity with other systems
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, source_id: int, target_id: int) -> None:
        if effect_type == "damage":
            self.get_data(target_id).hp -= effect_value * self.get_data(source_id).spell_modifier
        elif effect_type == "heal":
            self.get_data(target_id).hp += effect_value * self.get_data(source_id).spell_modifier
        elif effect_type == "hp":
            self.get_data(source_id).hp = effect_value