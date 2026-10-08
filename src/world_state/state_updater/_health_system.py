import math
from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class HealthEffect(str, Enum):
    APPLY_DAMAGE = "damage"
    APPLY_HEAL = "heal"
    APPLY_HP = "hp"
    IS_UNHITTABLE = "is_unhittable"


class HealthValidation(str, Enum):
    IS_SOURCE_HITTABLE = "is_source_hittable"
    IS_TARGET_HITTABLE = "is_target_hittable"


@dataclass(slots=True)
class ObjHealthData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    is_hittable: bool = False
    hp: float = 0.0
    spell_modifier: float = 1.0

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjHealthData":
        return cls(obj_id=game_obj.obj_id)


class HealthSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjHealthData, HealthEffect, HealthValidation)

    def get_data(self, obj_id: int) -> ObjHealthData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            display_obj.size = self._get_size(obj_id)
        return display_obj

    # ---- State Lookups ----

    def get_hp(self, obj_id: int) -> float:
        return self.get_data(obj_id).hp

    def _get_size(self, obj_id: int) -> float:
        obj_hp = self.get_data(obj_id).hp
        return 0.01 + math.sqrt(0.0001 * abs(obj_hp))

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case HealthValidation.IS_SOURCE_HITTABLE:
                return not self.get_data(source_id).is_hittable
            case HealthValidation.IS_TARGET_HITTABLE:
                return not self.get_data(target_id).is_hittable
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case HealthEffect.APPLY_DAMAGE:
                self.get_data(obj_id).hp -= effect_value
            case HealthEffect.APPLY_HEAL:
                self.get_data(obj_id).hp += effect_value
            case HealthEffect.APPLY_HP:
                self.get_data(obj_id).hp = effect_value
            case HealthEffect.IS_UNHITTABLE:
                data = self.get_data(obj_id)
                data.is_hittable = bool(effect_value)
        return triggered_spell_id