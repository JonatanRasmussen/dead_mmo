from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, ValuesView
from src.settings import Consts

@dataclass(slots=True)
class ObjCastingData:
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    gcd_start: int = -10000
    gcd_end: int = 0
    cooldown_start: int = -10000
    cooldown_end: int = 0
    selected_spell_id: int = Consts.EMPTY_ID
    casting_start: int = -10000
    casting_duration: int = 0
    casting_ticks: int = 0

class CastingEffect(str, Enum):
    APPLY_TICKS_ADDITION = "add_channeling_ticks"
    APPLY_TICKS_SUBTRACTION = "consume_channeling_ticks"
    APPLY_GCD = "gcd_duration"
    APPLY_COOLDOWN = "base_cooldown"
    APPLY_PARENT_CD = "apply_parent_cd"
    SELECT_SPELL_ID = "select_spell_id"

class CastingInvalidOutcomes(str, Enum):
    TICKS_NOT_READY = "out_of_channeling_ticks"
    GCD_NOT_READY = "gcd_not_ready"
    COOLDOWN_NOT_READY = "cooldown_not_ready"
    PARENT_COOLDOWN_NOT_READY = "parent_cooldown_not_ready"
    INVALID_SPELL_SELECTED = "invalid_spell_selected"

class CastingValidation(str, Enum):
    ARE_TICKS_READY = "has_channeling_ticks"
    IS_GCD_READY = "is_gcd_ready"
    IS_COOLDOWN_READY = "is_cooldown_ready"
    IS_PARENT_CD_READY = "is_parent_cooldown_ready"
    IS_SPELL_SELECTED = "is_spell_selected"


class CastingSystem:
    def __init__(self) -> None:
        self._data_dct: dict[int, ObjCastingData] = {}

    def spawn_game_obj(self, new_obj_id: int, parent_id: int) -> None:
        game_obj = ObjCastingData(obj_id=new_obj_id, parent_id=parent_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjCastingData(obj_id=obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjCastingData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjCastingData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id) # assertions check
        self._data_dct.pop(obj_id, None)

    # ---- Lookups ----
    def view_all_data(self) -> ValuesView[ObjCastingData]:
        return self._data_dct.values()

    def get_parent_data(self, obj_id: int) -> ObjCastingData:
        obj_data = self.get_data(obj_id)
        parent_id = obj_data.parent_id
        if parent_id == Consts.EMPTY_ID or parent_id == obj_id:
            print(f"Warning: Obj {obj_id}'s parent {parent_id} has unexpected configuration.")
            return obj_data
        return self.get_data(parent_id)

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int) -> str:
        if validation_type == CastingValidation.ARE_TICKS_READY:
            if self.get_data(source_id).casting_ticks < round(validation_value):
                return CastingInvalidOutcomes.TICKS_NOT_READY.value
        if validation_type == CastingValidation.IS_GCD_READY:
            if self.get_data(source_id).gcd_end > timestamp:
                return CastingInvalidOutcomes.GCD_NOT_READY.value
        if validation_type == CastingValidation.IS_COOLDOWN_READY:
            if self.get_data(source_id).cooldown_end > timestamp:
                return CastingInvalidOutcomes.COOLDOWN_NOT_READY.value
        if validation_type == CastingValidation.IS_PARENT_CD_READY:
            parent_data = self.get_parent_data(source_id)
            if parent_data.cooldown_end > timestamp:
                return CastingInvalidOutcomes.PARENT_COOLDOWN_NOT_READY.value
        if validation_type == CastingValidation.IS_SPELL_SELECTED:
            if self.get_data(source_id).selected_spell_id != round(validation_value):
                return CastingInvalidOutcomes.INVALID_SPELL_SELECTED.value
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int) -> None:
        if effect_type == CastingEffect.APPLY_TICKS_ADDITION:
            self.get_data(source_id).casting_ticks += round(effect_value)
        elif effect_type == CastingEffect.APPLY_TICKS_SUBTRACTION:
            self.get_data(source_id).casting_ticks -= max(0, round(effect_value))
        elif effect_type == CastingEffect.APPLY_GCD:
            other_data = self.get_data(source_id)
            other_data.gcd_start = timestamp
            other_data.gcd_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.APPLY_COOLDOWN:
            other_data = self.get_data(source_id)
            other_data.cooldown_start = timestamp
            other_data.cooldown_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.APPLY_PARENT_CD:
            parent_data = self.get_parent_data(source_id)
            parent_data.cooldown_start = timestamp
            parent_data.cooldown_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.SELECT_SPELL_ID:
            self.get_data(source_id).selected_spell_id = round(effect_value)