from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class PeriodicEffect(str, Enum):
    SET_PERIODIC_SPELL = "periodic_spell"
    SCHEDULE_PERIODIC_SPELL = "schedule_spell"
    TRIGGER_PERIODIC_SPELL = "trigger_spell"


class PeriodicValidation(str, Enum):
    IS_SCHEDULED_FOR_UPDATE = "is_scheduled_for_update"


@dataclass(slots=True)
class ObjPeriodicData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    spawn_timestamp: int = Consts.EMPTY_TIMESTAMP
    periodic_spell_id: int = Consts.EMPTY_SPELL_ID
    delay_between_ticks: int = 0

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjPeriodicData":
        return cls(
            obj_id=game_obj.obj_id,
            spawn_timestamp=game_obj.spawn_timestamp
        )


class PeriodicSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjPeriodicData, PeriodicEffect, PeriodicValidation)

    def get_data(self, obj_id: int) -> ObjPeriodicData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            pass  # Add display obj contributions from this system's data
        return display_obj

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case PeriodicValidation.IS_SCHEDULED_FOR_UPDATE:
                data = self.get_data(source_id)
                if data.delay_between_ticks <= 0:
                    return False
                delta = timestamp - data.spawn_timestamp
                if delta < data.delay_between_ticks:
                    return False
                tolerance = round(validation_value)
                return (delta % data.delay_between_ticks) < tolerance
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case PeriodicEffect.SET_PERIODIC_SPELL:
                self.get_data(obj_id).periodic_spell_id = round(effect_value)
            case PeriodicEffect.SCHEDULE_PERIODIC_SPELL:
                self.get_data(obj_id).delay_between_ticks = round(effect_value)
            case PeriodicEffect.TRIGGER_PERIODIC_SPELL:
                triggered_spell_id = Consts.EMPTY_SPELL_ID = self.get_data(obj_id).periodic_spell_id
        return triggered_spell_id