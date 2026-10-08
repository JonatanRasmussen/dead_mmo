import math
from dataclasses import dataclass
from enum import Enum
from typing import Tuple
from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj


class MovementEffect(str, Enum):
    WALK_FORWARD = "walk_forward"
    WALK_BACKWARD = "walk_backward"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    WALK_TOWARDS_TARGET = "walk_towards_target"
    STOP_WALK_TOWARDS_TARGET = "stop_walk_towards_target"
    TELEPORT_TO_TARGET = "teleport_to_target"
    PUSH_TARGET = "push_target"
    X_OFFSET = "x_offset"
    Y_OFFSET = "y_offset"
    MOVESPEED = "movespeed"
    ATTACH_TO_DESTINATION = "attach_to_destination"


class MovementValidation(str, Enum):
    IS_TARGET_THE_DESTINATION = Consts.IS_TARGETING_DESTINATION
    IS_WITHIN_RANGE_OF_DESTINATION = "is_destination_within_range"
    IS_SOURCE_ATTACHED = "is_source_attached"
    IS_TARGET_ATTACHED = "is_target_attached"


@dataclass(slots=True)
class ObjMovementData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    parent_id: int = Consts.EMPTY_OBJ_ID
    destination_id: int = Consts.EMPTY_OBJ_ID
    x_pos: float = 0.0
    y_pos: float = 0.0
    x_vel: float = 0.0
    y_vel: float = 0.0
    x_dir: float = 0.0
    y_dir: float = 0.0
    timestamp: int = 0
    movespeed: float = 1.0
    attached_to_id: int = Consts.EMPTY_OBJ_ID

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjMovementData":
        return cls(
            obj_id=game_obj.obj_id,
            parent_id=game_obj.parent_id,
            destination_id=game_obj.destination_id
        )


class MovementSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjMovementData, MovementEffect, MovementValidation)

    def get_data(self, obj_id: int) -> ObjMovementData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            display_obj.pos_xy = (self._get_position(obj_id, current_time))
        return display_obj

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case MovementValidation.IS_TARGET_THE_DESTINATION:
                return self.get_data(source_id).destination_id == target_id
            case MovementValidation.IS_WITHIN_RANGE_OF_DESTINATION:
                return self._is_within_range(timestamp, source_id, self.get_data(source_id).destination_id, validation_value)
            case MovementValidation.IS_SOURCE_ATTACHED:
                return self.get_data(source_id).attached_to_id != Consts.EMPTY_OBJ_ID
            case MovementValidation.IS_TARGET_ATTACHED:
                if target_id in self._data_dct or target_id in self._game_objs:
                    return self.get_data(target_id).attached_to_id != Consts.EMPTY_OBJ_ID
                return False
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case MovementEffect.WALK_FORWARD:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if bool(effect_value) is True:
                    data.y_dir = max(-1.0, min(1.0, data.y_dir + 1.0))
                else:
                    data.y_dir = max(-1.0, min(1.0, data.y_dir - 1.0))
            case MovementEffect.WALK_BACKWARD:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if bool(effect_value) is True:
                    data.y_dir = max(-1.0, min(1.0, data.y_dir - 1.0))
                else:
                    data.y_dir = max(-1.0, min(1.0, data.y_dir + 1.0))
            case MovementEffect.WALK_LEFT:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if bool(effect_value) is True:
                    data.x_dir = max(-1.0, min(1.0, data.x_dir - 1.0))
                else:
                    data.x_dir = max(-1.0, min(1.0, data.x_dir + 1.0))
            case MovementEffect.WALK_RIGHT:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if bool(effect_value) is True:
                    data.x_dir = max(-1.0, min(1.0, data.x_dir + 1.0))
                else:
                    data.x_dir = max(-1.0, min(1.0, data.x_dir - 1.0))
            case MovementEffect.WALK_TOWARDS_TARGET:
                data = self.get_data(obj_id)
                valid, dx, dy, dist, _, _ = self._get_target_vector(obj_id, data.destination_id, timestamp)
                if valid and dist > 0.0:
                    self._bake_position(obj_id, timestamp)
                    data.x_dir = dx / dist
                    data.y_dir = dy / dist
            case MovementEffect.STOP_WALK_TOWARDS_TARGET:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                data.x_dir, data.y_dir = 0.0, 0.0
            case MovementEffect.TELEPORT_TO_TARGET:
                data = self.get_data(obj_id)
                valid, _, _, _, tar_x, tar_y = self._get_target_vector(obj_id, data.destination_id, timestamp)
                if valid:
                    data.x_pos, data.y_pos = tar_x, tar_y
                    data.x_vel, data.y_vel, data.x_dir, data.y_dir = 0.0, 0.0, 0.0, 0.0
                    data.timestamp = timestamp
            case MovementEffect.PUSH_TARGET:
                data = self.get_data(obj_id)
                valid, dx, dy, dist, _, _ = self._get_target_vector(obj_id, data.destination_id, timestamp)
                if valid and dist > 0.0:
                    self._bake_position(obj_id, timestamp)
                    speed_per_ms = effect_value * Consts.GLOBAL_MOVESPEED_TO_USE / 1000.0
                    data.x_vel = (dx / dist) * speed_per_ms
                    data.y_vel = (dy / dist) * speed_per_ms
            case MovementEffect.X_OFFSET:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if data.parent_id in self._game_objs or data.parent_id in self._data_dct:
                    p_x, _ = self._get_position(data.parent_id, timestamp)
                    data.x_pos = p_x
                data.x_pos += effect_value
            case MovementEffect.Y_OFFSET:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if data.parent_id in self._game_objs or data.parent_id in self._data_dct:
                    _, p_y = self._get_position(data.parent_id, timestamp)
                    data.y_pos = p_y
                data.y_pos += effect_value
            case MovementEffect.MOVESPEED:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                data.movespeed = effect_value
            case MovementEffect.ATTACH_TO_DESTINATION:
                data = self.get_data(obj_id)
                if self._is_attachment_allowed(data):
                    data.attached_to_id = data.destination_id
                else:
                    print(f"Warning, attachment from {data.obj_id} to {data.destination_id} failed.")
        return triggered_spell_id

    def _is_attachment_allowed(self, data: ObjMovementData) -> bool:
        destination_data = self.get_data(data.destination_id)
        destination_of_destination = self.get_data(data.destination_id).destination_id
        return destination_of_destination == Consts.EMPTY_SPELL_ID or destination_of_destination == destination_data.obj_id

    def _get_velocity(self, data: ObjMovementData) -> Tuple[float, float]:
        if data.attached_to_id != Consts.EMPTY_OBJ_ID:
            return self._get_velocity(self.get_data(data.attached_to_id))

        dir_mag_sq = data.x_dir**2 + data.y_dir**2
        if dir_mag_sq > 1.0:
            mag = math.sqrt(dir_mag_sq)
            nx, ny = data.x_dir / mag, data.y_dir / mag
        else:
            nx, ny = data.x_dir, data.y_dir
        base_speed = data.movespeed * Consts.GLOBAL_MOVESPEED_TO_USE / 1000.0
        return (nx * base_speed) + data.x_vel, (ny * base_speed) + data.y_vel

    def _get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        data = self.get_data(obj_id)
        if data.attached_to_id != Consts.EMPTY_OBJ_ID:
            return self._get_position(data.attached_to_id, current_time)

        dt = current_time - data.timestamp
        vx, vy = self._get_velocity(data)
        return data.x_pos + (vx * dt), data.y_pos + (vy * dt)

    def _bake_position(self, obj_id: int, current_time: int) -> None:
        data = self.get_data(obj_id)
        dt = current_time - data.timestamp
        vx, vy = self._get_velocity(data)
        data.x_pos += vx * dt
        data.y_pos += vy * dt
        data.timestamp = current_time

    def _get_target_vector(self, source_id: int, target_id: int, timestamp: int) -> tuple[bool, float, float, float, float, float]:
        if (source_id not in self._data_dct and source_id not in self._game_objs) or (target_id not in self._data_dct and target_id not in self._game_objs):
            return False, 0.0, 0.0, 0.0, 0.0, 0.0
        tar_x, tar_y = self._get_position(target_id, timestamp)
        src_x, src_y = self._get_position(source_id, timestamp)
        dx, dy = tar_x - src_x, tar_y - src_y
        dist = math.hypot(dx, dy)
        return True, dx, dy, dist, tar_x, tar_y

    def _is_within_range(self, current_time: int, source_id: int, target_id: int, range_limit: float) -> bool:
        if range_limit <= 0.0: return True
        valid, _, _, dist, _, _ = self._get_target_vector(source_id, target_id, current_time)
        return valid and dist <= range_limit