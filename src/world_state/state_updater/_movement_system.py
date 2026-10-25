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
    PUSH_DEST = "push_dest"
    X_OFFSET = "x_displacement"
    Y_OFFSET = "y_displacement"
    MOVESPEED = "movespeed"
    ATTACH_TO_TARGET = "attach_to_target"


class MovementValidation(str, Enum):
    IS_DEST_THE_TARGET = Consts.IS_TARGETING_TARGET
    IS_WITHIN_RANGE_OF_DEST = "is_dest_within_range"
    IS_SOURCE_ATTACHED = "is_source_attached"
    IS_DEST_ATTACHED = "is_dest_attached"


@dataclass(slots=True)
class ObjMovementData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    parent_id: int = Consts.EMPTY_OBJ_ID
    target_id: int = Consts.EMPTY_OBJ_ID
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
            target_id=game_obj.target_id
        )

    def get_velocity(self) -> tuple[float, float]:
        dir_mag_sq = self.x_dir**2 + self.y_dir**2
        if dir_mag_sq > 1.0:
            mag = math.sqrt(dir_mag_sq)
            nx, ny = self.x_dir / mag, self.y_dir / mag
        else:
            nx, ny = self.x_dir, self.y_dir
        base_speed = self.movespeed * Consts.GLOBAL_MOVESPEED_TO_USE
        return (nx * base_speed) + self.x_vel, (ny * base_speed) + self.y_vel

    def get_position(self, current_time: int) -> tuple[float, float]:
        dt = current_time - self.timestamp
        vx, vy = self.get_velocity()
        return self.x_pos + (vx * dt), self.y_pos + (vy * dt)


class MovementSystem(BaseSystem[ObjMovementData]):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjMovementData, MovementEffect, MovementValidation)

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, dest_id: int) -> bool:
        match validation_type:
            case MovementValidation.IS_DEST_THE_TARGET:
                return self.get_data(source_id).target_id == dest_id
            case MovementValidation.IS_WITHIN_RANGE_OF_DEST:
                return self._is_within_range(timestamp, source_id, dest_id, float(validation_value))
            case MovementValidation.IS_SOURCE_ATTACHED:
                return self.get_data(source_id).attached_to_id != Consts.EMPTY_OBJ_ID
            case MovementValidation.IS_DEST_ATTACHED:
                if dest_id in self._data_dct or dest_id in self._game_objs:
                    return self.get_data(dest_id).attached_to_id != Consts.EMPTY_OBJ_ID
                return False
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
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
                valid, dx, dy, dist, _, _ = self._get_target_vector(obj_id, data.target_id, timestamp)
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
                valid, _, _, _, tar_x, tar_y = self._get_target_vector(obj_id, data.target_id, timestamp)
                if valid:
                    data.x_pos, data.y_pos = tar_x, tar_y
                    data.x_vel, data.y_vel, data.x_dir, data.y_dir = 0.0, 0.0, 0.0, 0.0
                    data.timestamp = timestamp
            case MovementEffect.PUSH_DEST:
                data = self.get_data(obj_id)
                valid, dx, dy, dist, _, _ = self._get_target_vector(obj_id, data.target_id, timestamp)
                if valid and dist > 0.0:
                    self._bake_position(obj_id, timestamp)
                    # Automatically scales the old normalized speed to logical pixels per ms
                    speed_per_ms = (effect_value / 100.0) * Consts.GLOBAL_MOVESPEED_TO_USE
                    data.x_vel = (dx / dist) * speed_per_ms
                    data.y_vel = (dy / dist) * speed_per_ms
            case MovementEffect.X_OFFSET:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if data.parent_id in self._game_objs or data.parent_id in self._data_dct:
                    p_x, _ = self.get_position(data.parent_id, timestamp)
                    data.x_pos = p_x
                data.x_pos += float(effect_value)
            case MovementEffect.Y_OFFSET:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                if data.parent_id in self._game_objs or data.parent_id in self._data_dct:
                    _, p_y = self.get_position(data.parent_id, timestamp)
                    data.y_pos = p_y
                data.y_pos += float(effect_value)
            case MovementEffect.MOVESPEED:
                data = self.get_data(obj_id)
                self._bake_position(obj_id, timestamp)
                data.movespeed = (effect_value / 100.0)
            case MovementEffect.ATTACH_TO_TARGET:
                data = self.get_data(obj_id)
                if self._is_attachment_allowed(data):
                    data.attached_to_id = data.target_id
                else:
                    print(f"Warning, attachment from {data.obj_id} to {data.target_id} failed.")
        return triggered_spell_id

    def _is_attachment_allowed(self, data: ObjMovementData) -> bool:
        target_data = self.get_data(data.target_id)
        target_of_target = self.get_data(data.target_id).target_id
        return target_of_target == Consts.EMPTY_SPELL_ID or target_of_target == target_data.obj_id

    def _get_velocity(self, obj_id: int) -> Tuple[float, float]:
        data = self.get_read_only_data(obj_id)
        if data.attached_to_id != Consts.EMPTY_OBJ_ID:
            return self._get_velocity(data.attached_to_id)
        return data.get_velocity()

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        data = self.get_read_only_data(obj_id)
        if data.attached_to_id != Consts.EMPTY_OBJ_ID:
            return self.get_position(data.attached_to_id, current_time)
        return data.get_position(current_time)

    def _bake_position(self, obj_id: int, current_time: int) -> None:
        data = self.get_data(obj_id)
        dt = current_time - data.timestamp
        vx, vy = self._get_velocity(obj_id)
        data.x_pos += vx * dt
        data.y_pos += vy * dt
        data.timestamp = current_time

    def _get_target_vector(self, source_id: int, dest_id: int, timestamp: int) -> tuple[bool, float, float, float, float, float]:
        if (source_id not in self._data_dct and source_id not in self._game_objs) or (dest_id not in self._data_dct and dest_id not in self._game_objs):
            return False, 0.0, 0.0, 0.0, 0.0, 0.0
        dest_x, dest_y = self.get_position(dest_id, timestamp)
        src_x, src_y = self.get_position(source_id, timestamp)
        dx, dy = dest_x - src_x, dest_y - src_y
        dist = math.hypot(dx, dy)
        return True, dx, dy, dist, dest_x, dest_y

    def _is_within_range(self, current_time: int, source_id: int, dest_id: int, range_limit: float) -> bool:
        if range_limit <= 0.0: return True
        valid, _, _, dist, _, _ = self._get_target_vector(source_id, dest_id, current_time)
        return valid and dist <= range_limit