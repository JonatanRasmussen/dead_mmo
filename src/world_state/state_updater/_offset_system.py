from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class OffsetEffect(str, Enum):
    OFFSET_X = "offset_x"
    OFFSET_Y = "offset_y"
    ANCHOR_TO_DESTINATION = "anchor_to_destination"


class OffsetValidation(str, Enum):
    pass


@dataclass(slots=True)
class ObjOffsetData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    destination_id: int = Consts.EMPTY_OBJ_ID
    x_offset: float = 0.0
    y_offset: float = 0.0
    is_anchored: bool = False

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjOffsetData":
        return cls(
            obj_id=game_obj.obj_id,
            destination_id=game_obj.destination_id
        )


class OffsetSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjOffsetData, OffsetEffect, OffsetValidation)

    def get_data(self, obj_id: int) -> ObjOffsetData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            display_obj.offset_xy = self._get_total_offset(obj_id)
        return display_obj

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case OffsetEffect.OFFSET_X:
                self.get_data(obj_id).x_offset = effect_value / 1000.0
            case OffsetEffect.OFFSET_Y:
                self.get_data(obj_id).y_offset = effect_value / 1000.0
            case OffsetEffect.ANCHOR_TO_DESTINATION:
                data = self.get_data(obj_id)
                if bool(effect_value):
                    if self._is_anchor_allowed(data.destination_id):
                        data.is_anchored = True
                    else:
                        print(f"Warning, anchoring from {data.obj_id} to {data.destination_id} failed.")
                else:
                    data.is_anchored = False
        return triggered_spell_id

    def _is_anchor_allowed(self, dest_id: int) -> bool:
        if dest_id == Consts.EMPTY_OBJ_ID or (dest_id not in self._game_objs and dest_id not in self._data_dct):
            return False
        next_dest = self.get_data(dest_id).destination_id
        if next_dest == Consts.EMPTY_OBJ_ID or next_dest == dest_id:
            return True
        return self._is_anchor_allowed(next_dest)

    def _get_total_offset(self, obj_id: int) -> tuple[float, float]:
        data = self.get_data(obj_id)
        if not data.is_anchored or data.destination_id == Consts.EMPTY_OBJ_ID or data.destination_id == obj_id:
            return data.x_offset, data.y_offset
        if data.destination_id not in self._game_objs and data.destination_id not in self._data_dct:
            return data.x_offset, data.y_offset
        parent_x, parent_y = self._get_total_offset(data.destination_id)
        return data.x_offset + parent_x, data.y_offset + parent_y