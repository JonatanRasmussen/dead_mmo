from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class IdentityEffect(str, Enum):
    ASSIGN_TO_FACTION = "assign_to_faction"
    APPLY_PLAYER_NUMBER = "player_number"


class IdentityValidation(str, Enum):
    IS_SOURCE_TARGETING_SELF = Consts.IS_TARGETING_SELF
    IS_SOURCE_TARGETING_PARENT = "is_targeting_parent"
    IS_SOURCE_TARGET_OF_DEST = "is_source_target_of_dest"
    IS_DEST_OTHER_FACTION = "is_dest_other_faction"


@dataclass(slots=True)
class ObjIdentityData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    parent_id: int = Consts.EMPTY_OBJ_ID
    target_id: int = Consts.EMPTY_OBJ_ID
    player_number: int = 0
    faction_id: int = 0

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> 'ObjIdentityData':
        return cls(
            obj_id=game_obj.obj_id,
            parent_id=game_obj.parent_id,
            target_id=game_obj.target_id
        )


class IdentitySystem(BaseSystem[ObjIdentityData]):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjIdentityData, IdentityEffect, IdentityValidation)

    def get_current_target_for_obj(self, obj_id: int) -> int:
        if obj_id in self._game_objs or obj_id in self._data_dct:
            return self.get_data(obj_id).target_id
        return ObjIdentityData().target_id

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, dest_id: int) -> bool:
        match validation_type:
            case IdentityValidation.IS_SOURCE_TARGETING_SELF:
                return bool(validation_value) == (source_id == dest_id)
            case IdentityValidation.IS_SOURCE_TARGETING_PARENT:
                return bool(validation_value) == (self.get_data(source_id).parent_id == dest_id)
            case IdentityValidation.IS_SOURCE_TARGET_OF_DEST:
                return bool(validation_value) == (self.get_data(dest_id).target_id == source_id)
            case IdentityValidation.IS_DEST_OTHER_FACTION:
                src_faction = self.get_data(source_id).faction_id
                dest_faction = self.get_data(dest_id).faction_id
                if src_faction == 0 or dest_faction == 0:
                    return False
                is_different = (src_faction != dest_faction)
                return is_different == bool(validation_value)
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case IdentityEffect.APPLY_PLAYER_NUMBER:
                self.get_data(obj_id).player_number += effect_value
            case IdentityEffect.ASSIGN_TO_FACTION:
                self.get_data(obj_id).faction_id = effect_value
        return triggered_spell_id