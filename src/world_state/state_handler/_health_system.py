import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from src.settings import Consts

@dataclass(slots=True)
class ObjHealthData:
    obj_id: int = Consts.EMPTY_ID
    hp: float = 0.0
    spell_modifier: float = 1.0

    @classmethod
    def create_new_obj(cls, new_obj_id: int) -> "ObjHealthData":
        return cls(
            obj_id=new_obj_id,
        )

class HealthEffect(str, Enum):
    APPLY_DAMAGE = "damage"
    APPLY_HEAL = "heal"
    APPLY_HP = "hp"

class HealthInvalidOutcomes(str, Enum):
    pass

class HealthValidation(str, Enum):
    pass

class HealthSystem:

    def __init__(self) -> None:
        self._data_dct: Dict[int, ObjHealthData] = {}

    def spawn_game_obj(self, new_obj_id: int) -> None:
        game_obj = ObjHealthData.create_new_obj(new_obj_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjHealthData.create_new_obj(obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjHealthData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjHealthData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

    # ---- State Lookups ----

    def get_hp(self, obj_id: int) -> float:
        return self.get_data(obj_id).hp

    def get_size(self, obj_id: int) -> float:
        obj_hp = self.get_data(obj_id).hp
        return 0.01 + math.sqrt(0.0001 * abs(obj_hp))

    def validate_event(self) -> str:
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, source_id: int, target_id: int) -> None:
        if effect_type == HealthEffect.APPLY_DAMAGE:
            self.get_data(target_id).hp -= effect_value * self.get_data(source_id).spell_modifier
        elif effect_type == HealthEffect.APPLY_HEAL:
            self.get_data(target_id).hp += effect_value * self.get_data(source_id).spell_modifier
        elif effect_type == HealthEffect.APPLY_HP:
            self.get_data(source_id).hp = effect_value