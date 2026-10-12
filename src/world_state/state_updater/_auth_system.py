from src.world_state.state_updater.game_obj import GameObj


from dataclasses import dataclass
from enum import Enum
from typing import ValuesView
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class AuthEffect(str, Enum):
    SPAWN_AS_CHILD = "spawn_as_child"

class AuthValidation(str, Enum):
    IS_SOURCE_TARGETING_SELF = Consts.IS_TARGETING_SELF
    IS_TARGET_DESTINATION_OF_SOURCE = Consts.IS_TARGETING_DESTINATION
    IS_SOURCE_DESTINATION_OF_TARGET = Consts.IS_SOURCE_DESTINATION_OF_TARGET


class AuthSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, GameObj, AuthEffect, AuthValidation)
        self._next_obj_id: int = Consts.EMPTY_OBJ_ID + 1_000_000

    def get_data(self, obj_id: int) -> GameObj:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            pass  # Add display obj contributions from this system's data
        return display_obj

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case AuthValidation.IS_SOURCE_TARGETING_SELF:
                return bool(validation_value) == (source_id == target_id)
            case AuthValidation.IS_TARGET_DESTINATION_OF_SOURCE:
                return bool(validation_value) == (self.get_data(source_id).destination_id == target_id)
            case AuthValidation.IS_SOURCE_DESTINATION_OF_TARGET:
                return bool(validation_value) == (self.get_data(target_id).destination_id == source_id)
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case AuthEffect.SPAWN_AS_CHILD:
                new_obj_id = self._next_obj_id
                self._next_obj_id += 1
                game_obj = GameObj.create_new(new_obj_id, timestamp, Consts.EMPTY_OBJ_ID, round(effect_value), obj_id)
                self._game_objs[new_obj_id] = game_obj
        return triggered_spell_id