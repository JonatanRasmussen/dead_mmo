from dataclasses import dataclass
from enum import Enum
from typing import ValuesView
from src.settings import Consts
from .system_interface import DisplayObj, GameObj, System


class CastingEffect(str, Enum):
    GAIN_CHANNELING_TICKS = "gain_channeling_ticks"
    APPLY_GCD = "gcd_duration"
    APPLY_COOLDOWN = "base_cooldown"
    APPLY_PARENT_CD = "apply_parent_cd"
    SELECT_SPELL_ID = "select_spell_id"


class CastingValidation(str, Enum):
    HAS_CHANNELING_TICKS = "has_channeling_ticks"
    IS_GCD_READY = "is_gcd_ready"
    IS_COOLDOWN_READY = "is_cooldown_ready"
    IS_PARENT_CD_READY = "is_parent_cooldown_ready"
    IS_SPELL_SELECTED = "is_spell_selected"


@dataclass(slots=True)
class ObjCastingData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    parent_id: int = Consts.EMPTY_OBJ_ID
    gcd_start: int = Consts.EMPTY_TIMESTAMP
    gcd_duration: int = 0
    cooldown_start: int = Consts.EMPTY_TIMESTAMP
    cooldown_duration: int = 0
    selected_spell_id: int = Consts.EMPTY_SPELL_ID
    casting_start: int = Consts.EMPTY_TIMESTAMP
    casting_duration: int = 0
    casting_ticks: int = 0

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> 'ObjCastingData':
        return ObjCastingData(obj_id=game_obj.obj_id, parent_id=game_obj.parent_id)


class CastingSystem(System):

    def __init__(self) -> None:
        self._game_objs: dict[int, GameObj] = {}
        self._data_dct: dict[int, ObjCastingData] = {}

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            pass  # Add display obj contributions from this system's data
        return display_obj

    def get_effect_types(self) -> set[str]:
        return {e.value for e in CastingEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in CastingValidation}

    def spawn_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self._game_objs, f"Error: GameObj {game_obj.obj_id} already exist."
        self._game_objs[game_obj.obj_id] = game_obj

    def get_data(self, obj_id: int) -> ObjCastingData:
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]
        assert obj_id in self._game_objs, f"Error: GameObj {obj_id} does not exist."
        game_obj = self._game_objs[obj_id]
        data = ObjCastingData.create_from_game_obj(game_obj)
        self._data_dct[obj_id] = data
        return data

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # assertions check
        self._data_dct.pop(obj_id, None)

    # ---- Lookups ----
    def view_all_data(self) -> ValuesView[ObjCastingData]:
        return self._data_dct.values()

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
                return self._get_gcd_end_timestamp(source_id) <= timestamp
            case CastingValidation.IS_COOLDOWN_READY:
                return self._get_cooldown_end_timestamp(source_id) <= timestamp
            case CastingValidation.IS_PARENT_CD_READY:
                return self._get_cooldown_end_timestamp(self.get_parent_data(source_id).obj_id) <= timestamp
            case CastingValidation.IS_SPELL_SELECTED:
                return self.get_data(source_id).selected_spell_id == round(validation_value)
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> None:
        match effect_type:
            case CastingEffect.GAIN_CHANNELING_TICKS:
                data = self.get_data(obj_id)
                data.casting_ticks += round(effect_value)
                data.casting_ticks = max(0, data.casting_ticks)
            case CastingEffect.APPLY_GCD:
                other_data = self.get_data(obj_id)
                other_data.gcd_start = timestamp
                other_data.gcd_duration = round(effect_value)
            case CastingEffect.APPLY_COOLDOWN:
                other_data = self.get_data(obj_id)
                other_data.cooldown_start = timestamp
                other_data.cooldown_duration = round(effect_value)
            case CastingEffect.APPLY_PARENT_CD:
                parent_data = self.get_parent_data(obj_id)
                parent_data.cooldown_start = timestamp
                parent_data.cooldown_duration = round(effect_value)
            case CastingEffect.SELECT_SPELL_ID:
                self.get_data(obj_id).selected_spell_id = round(effect_value)

    def _get_cast_end_timestamp(self, obj_id: int) -> int:
        data = self.get_data(obj_id)
        return data.casting_start + data.casting_duration

    def _get_cooldown_end_timestamp(self, obj_id: int) -> int:
        data = self.get_data(obj_id)
        return data.cooldown_start + data.cooldown_duration

    def _get_gcd_end_timestamp(self, obj_id: int) -> int:
        data = self.get_data(obj_id)
        return data.gcd_start + data.gcd_duration