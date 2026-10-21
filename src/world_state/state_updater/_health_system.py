import math
from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class HealthEffect(str, Enum):
    APPLY_DAMAGE = "damage"
    APPLY_HEAL = "heal"
    APPLY_HP = "hp"
    IS_HITTABLE = "is_hittable"


class HealthValidation(str, Enum):
    IS_SOURCE_HITTABLE = "is_source_hittable"
    IS_DEST_HITTABLE = "is_dest_hittable"


@dataclass(slots=True)
class ObjHealthData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    is_hittable: bool = False
    hp: float = 0.0
    spell_modifier: float = 1.0

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjHealthData":
        return cls(obj_id=game_obj.obj_id)

    @property
    def size(self) -> float:
        return 64.0


class HealthSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjHealthData, HealthEffect, HealthValidation)

    def get_data(self, obj_id: int) -> ObjHealthData:
        return super().get_data(obj_id)

    def get_hp(self, obj_id: int) -> float:
        return self.get_data(obj_id).hp

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, dest_id: int) -> bool:
        match validation_type:
            case HealthValidation.IS_SOURCE_HITTABLE:
                return self.get_data(source_id).is_hittable
            case HealthValidation.IS_DEST_HITTABLE:
                return self.get_data(dest_id).is_hittable
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case HealthEffect.APPLY_DAMAGE:
                self.get_data(obj_id).hp -= float(effect_value)
            case HealthEffect.APPLY_HEAL:
                self.get_data(obj_id).hp += float(effect_value)
            case HealthEffect.APPLY_HP:
                self.get_data(obj_id).hp = float(effect_value)
            case HealthEffect.IS_HITTABLE:
                data = self.get_data(obj_id)
                data.is_hittable = bool(effect_value)
        return triggered_spell_id