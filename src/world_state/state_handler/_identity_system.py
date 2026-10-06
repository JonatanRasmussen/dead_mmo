from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class IdentityEffect(str, Enum):
    SWAP_TEAM = "teamswap"
    THREAT_SCORE = "threat_score"
    APPLY_PLAYER_NUMBER = "player_number"


class IdentityValidation(str, Enum):
    IS_SOURCE_TARGETING_SELF = "is_targeting_self"
    IS_SOURCE_TARGETING_PARENT = "is_targeting_parent"
    IS_TARGET_OTHER_TEAM = "is_target_other_team"


@dataclass(slots=True)
class ObjIdentityData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    parent_id: int = Consts.EMPTY_OBJ_ID
    event_target_id: int = Consts.EMPTY_OBJ_ID
    player_number: int = 0
    threat_score: int = 0
    is_enemy: bool = False

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> 'ObjIdentityData':
        return cls(
            obj_id=game_obj.obj_id,
            parent_id=game_obj.parent_id,
            event_target_id=game_obj.destination_id
        )


class IdentitySystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjIdentityData, IdentityEffect, IdentityValidation)

    def get_data(self, obj_id: int) -> ObjIdentityData:
        # IdentitySystem has custom logic on creation to inherit enemy status
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]

        data: ObjIdentityData = super().get_data(obj_id)
        if data.parent_id in self._game_objs or data.parent_id in self._data_dct:
            data.is_enemy = self.get_data(data.parent_id).is_enemy
        return data

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            pass  # Add display obj contributions from this system's data
        return display_obj

    def get_parent_data(self, obj_id: int) -> ObjIdentityData:
        obj_data = self.get_data(obj_id)
        parent_id = obj_data.parent_id
        if parent_id == Consts.EMPTY_OBJ_ID or parent_id == obj_id:
            print(f"Warning: Obj {obj_id}'s parent {parent_id} has unexpected configuration.")
            return obj_data
        return self.get_data(parent_id)

    def get_current_target_for_obj(self, obj_id: int) -> int:
        if obj_id in self._game_objs or obj_id in self._data_dct:
            return self.get_data(obj_id).event_target_id
        return ObjIdentityData().event_target_id

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case IdentityValidation.IS_SOURCE_TARGETING_SELF:
                return bool(validation_value) == (source_id == target_id)
            case IdentityValidation.IS_SOURCE_TARGETING_PARENT:
                return bool(validation_value) == (self.get_data(source_id).parent_id == target_id)
            case IdentityValidation.IS_TARGET_OTHER_TEAM:
                return bool(validation_value) == (self.get_data(source_id).is_enemy != self.get_data(target_id).is_enemy)
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        match effect_type:
            case IdentityEffect.APPLY_PLAYER_NUMBER:
                self.get_data(obj_id).player_number += int(effect_value)
                return Consts.EMPTY_SPELL_ID
            case IdentityEffect.SWAP_TEAM:
                data = self.get_data(obj_id)
                data.is_enemy = not data.is_enemy
                return Consts.EMPTY_SPELL_ID
            case _:
                return Consts.EMPTY_SPELL_ID