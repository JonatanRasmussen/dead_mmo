from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .system_interface import System, DisplayObj


class IdentityEffect(str, Enum):
    TARGETSWAP_TO_EVENT_TARGET = "targetswap_to_event_target"
    TARGETSWAP_TO_PARENT = "targetswap_to_parent"
    TARGETSWAP_TO_PARENTS_TARGET = "targetswap_to_parents_target"
    SWAP_TEAM = "teamswap"
    THREAT_SCORE = "threat_score"
    APPLY_PLAYER_NUMBER = "player_number"


class IdentityValidation(str, Enum):
    IS_SOURCE_TARGETING_SELF = "is_targeting_self"
    IS_TARGET_OTHER_TEAM = "is_target_other_team"


@dataclass(slots=True)
class ObjIdentityData:
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    event_target_id: int = Consts.EMPTY_ID
    player_number: int = 0
    threat_score: int = 0
    is_enemy: bool = False


class IdentitySystem(System):

    def __init__(self) -> None:
        self._data_dct: dict[int, ObjIdentityData] = {}
        self.player_id: int = Consts.EMPTY_ID
        self.boss_id: int = Consts.EMPTY_ID

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        return display_obj

    def get_effect_types(self) -> set[str]:
        return {e.value for e in IdentityEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in IdentityValidation}

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, parent_id: int, spell_id: int, target_id: int) -> None:
        is_enemy = self.get_data(parent_id).is_enemy if parent_id in self._data_dct else False
        game_obj = ObjIdentityData(obj_id=new_obj_id, parent_id=parent_id, event_target_id=target_id, is_enemy=is_enemy)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjIdentityData(obj_id=obj_id, event_target_id=obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjIdentityData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjIdentityData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self._data_dct.pop(obj_id, None)

    def get_parent_data(self, obj_id: int) -> ObjIdentityData:
        obj_data = self.get_data(obj_id)
        parent_id = obj_data.parent_id
        if parent_id == Consts.EMPTY_ID or parent_id == obj_id:
            print(f"Warning: Obj {obj_id}'s parent {parent_id} has unexpected configuration.")
            return obj_data
        return self.get_data(parent_id)

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self._data_dct.get(obj_id, ObjIdentityData()).event_target_id

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        if validation_type == IdentityValidation.IS_TARGET_OTHER_TEAM:
            return bool(validation_value) == (self.get_data(source_id).is_enemy != self.get_data(target_id).is_enemy)
        return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, target_id: int) -> None:
        if effect_type == IdentityEffect.TARGETSWAP_TO_EVENT_TARGET:
            self.get_data(source_id).event_target_id = target_id
        elif effect_type == IdentityEffect.TARGETSWAP_TO_PARENT:
            data = self.get_data(source_id)
            data.event_target_id = data.parent_id
        elif effect_type == IdentityEffect.TARGETSWAP_TO_PARENTS_TARGET:
            data = self.get_data(source_id)
            parent_data = self.get_parent_data(source_id)
            data.event_target_id = parent_data.event_target_id
        elif effect_type == IdentityEffect.APPLY_PLAYER_NUMBER:
            self.get_data(source_id).player_number += int(effect_value)
            self.player_id = source_id
        elif effect_type == IdentityEffect.APPLY_PLAYER_NUMBER:
            self.get_data(source_id).player_number += int(effect_value)
            self.player_id = source_id
        elif effect_type == IdentityEffect.SWAP_TEAM:
            data = self.get_data(source_id)
            data.is_enemy = not data.is_enemy