from dataclasses import dataclass
from enum import Enum
from typing import ValuesView
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class CastingEffect(str, Enum):
    GAIN_CASTING_TICKS = "gain_casting_ticks"
    BEGIN_CAST = "begin_cast"
    APPLY_COOLDOWN = "add_cooldown"
    SELECT_SPELL_ID = "select_spell_id"
    BIND_TO_INPUT_ID = "bind_to_input_id"
    TRY_CAST_SELECTED_SPELL = "try_cast_selected_spell"
    DISPLAY_PARENTS_CD = "display_parents_cd"
    STOP_CAST = "stop_cast"


class CastingValidation(str, Enum):
    HAS_CASTING_TICKS = "has_casting_ticks"
    IS_CAST_IN_PROGRESS = "is_cast_in_progress"
    IS_SHARED_CASTBAR_AVAILABLE = "is_shared_castbar_available"
    IS_GCD_READY = "is_gcd_ready"
    IS_COOLDOWN_READY = "is_cd_ready"
    IS_PARENT_CD_READY = "is_parent_cooldown_ready"
    IS_SPELL_SELECTED = "is_spell_selected"
    IS_BOUND_TO_INPUT_ID = "is_bound_to_input_id"


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

    @property
    def casting_end(self) -> int:
        return self.casting_start + self.casting_duration

    @property
    def cooldown_end(self) -> int:
        return self.cooldown_start + self.cooldown_duration

    def get_cooldown_progress(self, current_time: int) -> float:
        if self.cooldown_duration <= 0:
            return 0.0
        elapsed_time = current_time - self.cooldown_start
        progress = elapsed_time / self.cooldown_duration
        return max(0.0, min(1.0, progress))

    def get_castbar_progress(self, current_time: int) -> float:
        if self.casting_duration <= 0:
            return 0.0
        elapsed_time = current_time - self.casting_start
        progress = elapsed_time / self.casting_duration
        return max(0.0, min(1.0, progress))

class CastingSystem(BaseSystem[ObjCastingData]):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjCastingData, CastingEffect, CastingValidation)

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, dest_id: int) -> bool:
        match validation_type:
            case CastingValidation.HAS_CASTING_TICKS:
                return self.get_data(source_id).casting_ticks >= validation_value
            case CastingValidation.IS_CAST_IN_PROGRESS:
                return (self.get_data(source_id).casting_end >= timestamp) == bool(validation_value)
            case CastingValidation.IS_SHARED_CASTBAR_AVAILABLE:
                return (self.get_data(dest_id).casting_end <= timestamp) == bool(validation_value)
            case CastingValidation.IS_GCD_READY:
                return (self.get_data(dest_id).cooldown_end <= timestamp) == bool(validation_value)
            case CastingValidation.IS_COOLDOWN_READY:
                return (self.get_data(source_id).cooldown_end <= timestamp) == bool(validation_value)
            case CastingValidation.IS_PARENT_CD_READY:
                return (self.get_data(self.get_data(source_id).parent_id).cooldown_end <= timestamp) == bool(validation_value)
            case CastingValidation.IS_SPELL_SELECTED:
                return self.get_data(dest_id).selected_spell_id == validation_value
            case CastingValidation.IS_BOUND_TO_INPUT_ID:
                return self.get_data(dest_id).bound_input_id == validation_value
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case CastingEffect.GAIN_CASTING_TICKS:
                data = self.get_data(obj_id)
                data.casting_ticks += effect_value
                data.casting_ticks = max(0, data.casting_ticks)
            case CastingEffect.BEGIN_CAST:
                data = self.get_data(obj_id)
                data.casting_start = timestamp
                data.casting_duration = effect_value
            case CastingEffect.APPLY_COOLDOWN:
                data = self.get_data(obj_id)
                data.cooldown_start = timestamp
                data.cooldown_duration = effect_value
            case CastingEffect.SELECT_SPELL_ID:
                self.get_data(obj_id).selected_spell_id = effect_value
            case CastingEffect.BIND_TO_INPUT_ID:
                self.get_data(obj_id).bound_input_id = effect_value
            case CastingEffect.STOP_CAST:
                self.get_data(obj_id).selected_spell_id = Consts.EMPTY_SPELL_ID
            case CastingEffect.TRY_CAST_SELECTED_SPELL:
                data = self.get_data(obj_id)
                if bool(effect_value):
                    triggered_spell_id  = data.selected_spell_id
                else:  # Stop the cast that is currently in progress
                    data.casting_start = Consts.EMPTY_TIMESTAMP
                    data.casting_duration = 0
                    data.casting_ticks = 1
        return triggered_spell_id