from dataclasses import dataclass
from enum import Enum
from typing import ValuesView
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class CastingEffect(str, Enum):
    GAIN_CHANNELING_TICKS = "gain_channeling_ticks"
    APPLY_COOLDOWN = "add_cooldown"
    SELECT_SPELL_ID = "select_spell_id"
    BIND_TO_INPUT_ID = "bind_to_input_id"
    TRY_CAST_SELECTED_SPELL = "try_cast_selected_spell"


class CastingValidation(str, Enum):
    HAS_CHANNELING_TICKS = "has_channeling_ticks"
    IS_GCD_READY = "is_gcd_ready"
    IS_COOLDOWN_READY = "is_cd_ready"
    IS_PARENT_CD_READY = "is_parent_cooldown_ready"
    IS_SPELL_SELECTED = "is_spell_selected"
    IS_BOUND_TO_INPUT_ID = Consts.IS_BOUND_TO_INPUT_ID


@dataclass(slots=True)
class ObjCastingData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    parent_id: int = Consts.EMPTY_OBJ_ID
    cooldown_start: int = Consts.EMPTY_TIMESTAMP
    cooldown_duration: int = 0
    selected_spell_id: int = Consts.EMPTY_SPELL_ID
    bound_input_id: int = Consts.EMPTY_INPUT_ID
    casting_start: int = Consts.EMPTY_TIMESTAMP
    casting_duration: int = 0
    casting_ticks: int = 0

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> 'ObjCastingData':
        return ObjCastingData(obj_id=game_obj.obj_id, parent_id=game_obj.parent_id)


class CastingSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjCastingData, CastingEffect, CastingValidation)

    def get_data(self, obj_id: int) -> ObjCastingData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            pass  # Add display obj contributions from this system's data
        return display_obj

    def get_parent_data(self, obj_id: int) -> ObjCastingData:
        obj_data = self.get_data(obj_id)
        parent_id = obj_data.parent_id
        if parent_id == Consts.EMPTY_OBJ_ID or parent_id == obj_id:
            print(f"Warning: Obj {obj_id}'s parent {parent_id} has unexpected configuration.")
            return obj_data
        return self.get_data(parent_id)

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case CastingValidation.HAS_CHANNELING_TICKS:
                return self.get_data(source_id).casting_ticks >= round(validation_value)
            case CastingValidation.IS_GCD_READY:
                return self._get_cooldown_end_timestamp(target_id) <= timestamp
            case CastingValidation.IS_COOLDOWN_READY:
                return self._get_cooldown_end_timestamp(source_id) <= timestamp
            case CastingValidation.IS_PARENT_CD_READY:
                return self._get_cooldown_end_timestamp(self.get_parent_data(source_id).obj_id) <= timestamp
            case CastingValidation.IS_SPELL_SELECTED:
                return self.get_data(target_id).selected_spell_id == round(validation_value)
            case CastingValidation.IS_BOUND_TO_INPUT_ID:
                return self.get_data(target_id).bound_input_id == round(validation_value)
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case CastingEffect.GAIN_CHANNELING_TICKS:
                data = self.get_data(obj_id)
                data.casting_ticks += round(effect_value)
                data.casting_ticks = max(0, data.casting_ticks)
            case CastingEffect.APPLY_COOLDOWN:
                data = self.get_data(obj_id)
                data.cooldown_start = timestamp
                data.cooldown_duration = round(effect_value)
            case CastingEffect.SELECT_SPELL_ID:
                self.get_data(obj_id).selected_spell_id = round(effect_value)
            case CastingEffect.BIND_TO_INPUT_ID:
                self.get_data(obj_id).bound_input_id = round(effect_value)
            case CastingEffect.TRY_CAST_SELECTED_SPELL:
                data = self.get_data(obj_id)
                if bool(effect_value):
                    triggered_spell_id  = data.selected_spell_id
                else:  # Stop the cast that is currently in progress
                    data.casting_start = Consts.EMPTY_TIMESTAMP
                    data.casting_duration = 0
                    data.casting_ticks = 0
        return triggered_spell_id

    def _get_cast_end_timestamp(self, obj_id: int) -> int:
        data = self.get_data(obj_id)
        return data.casting_start + data.casting_duration

    def _get_cooldown_end_timestamp(self, obj_id: int) -> int:
        data = self.get_data(obj_id)
        return data.cooldown_start + data.cooldown_duration