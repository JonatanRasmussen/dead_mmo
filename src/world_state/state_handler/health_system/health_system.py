import math
from dataclasses import dataclass
from typing import Dict

@dataclass(slots=True)
class ObjHealthData:
    hp: float
    max_hp: float
    spell_modifier: float = 1.0
    is_environment: bool = False

    @classmethod
    def create_environment(cls) -> 'ObjHealthData':
        return cls(hp=0.0, max_hp=0.0, spell_modifier=1.0, is_environment=True)

    @classmethod
    def create_spawned(cls) -> 'ObjHealthData':
        return cls(hp=0.0, max_hp=0.0, spell_modifier=1.0, is_environment=False)

class HealthSystem:
    def __init__(self) -> None:
        self.game_obj_data_dct: Dict[int, ObjHealthData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjHealthData.create_environment()

    def spawn_game_obj(self, new_obj_id: int) -> None:
        if new_obj_id in self.game_obj_data_dct: return
        self.game_obj_data_dct[new_obj_id] = ObjHealthData.create_spawned()

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    # ---- State Update Handlers ----

    def damage_target(self, source_id: int, target_id: int, amount: float) -> None:
        source_data = self.game_obj_data_dct.get(source_id)
        target_data = self.game_obj_data_dct.get(target_id)
        if source_data and target_data:
            target_data.hp -= amount * source_data.spell_modifier

    def heal_target(self, source_id: int, target_id: int, amount: float) -> None:
        source_data = self.game_obj_data_dct.get(source_id)
        target_data = self.game_obj_data_dct.get(target_id)
        if source_data and target_data:
            target_data.hp += amount * source_data.spell_modifier

    # ---- State Lookups ----

    def get_hp(self, obj_id: int) -> float:
        if obj_id in self.game_obj_data_dct:
            return self.game_obj_data_dct[obj_id].hp
        return 0.0

    def get_size(self, obj_id: int) -> float:
        if obj_id not in self.game_obj_data_dct: return 0.0
        data = self.game_obj_data_dct[obj_id]
        if data.is_environment: return 0.0
        return 0.01 + math.sqrt(0.0001 * abs(data.hp))

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if effect_type == "damage":
            self.damage_target(source_id, target_id, effect_value)
        elif effect_type == "heal":
            self.heal_target(source_id, target_id, effect_value)
        elif effect_type == "hp":
            if data := self.game_obj_data_dct.get(source_id):
                data.hp = effect_value
                data.max_hp = effect_value