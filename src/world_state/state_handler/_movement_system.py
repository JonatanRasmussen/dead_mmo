import math
from dataclasses import dataclass
from enum import Enum
from typing import Tuple
from src.settings import Consts
from .system_interface import System, DisplayObj


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


class MovementValidation(str, Enum):
    IS_TARGET_THE_DESTINATION = "is_target_the_destination"
    IS_WITHIN_RANGE_OF_DESTINATION = "is_destination_within_range"


@dataclass(slots=True)
class ObjMovementData:
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    destination_id: int = Consts.EMPTY_ID
    x_pos: float = 0.0
    y_pos: float = 0.0
    x_vel: float = 0.0
    y_vel: float = 0.0
    x_dir: float = 0.0
    y_dir: float = 0.0
    timestamp: int = 0
    movespeed: float = 1.0

    @classmethod
    def create_new_obj(cls, new_obj_id: int, parent_id: int, destination_id: int) -> "ObjMovementData":
        return cls(
            obj_id=new_obj_id,
            parent_id=parent_id,
            destination_id=destination_id
        )


class MovementSystem(System):

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        display_obj.pos_xy = (self.get_position(obj_id, current_time))
        return display_obj

    def get_effect_types(self) -> set[str]:
        return {e.value for e in MovementEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in MovementValidation}

    def __init__(self) -> None:
        self._data_dct: dict[int, ObjMovementData] = {}

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, parent_id: int, spell_id: int, target_id: int) -> None:
        game_obj = ObjMovementData.create_new_obj(new_obj_id, parent_id, target_id)
        self.add_data(game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjMovementData(obj_id=obj_id)
        self.add_data(environment_obj)

    def add_data(self, new_obj: ObjMovementData) -> None:
        assert new_obj.obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj.obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjMovementData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

    # ---- Utilities ----

    def get_velocity(self, data: ObjMovementData) -> Tuple[float, float]:
        dir_mag_sq = data.x_dir**2 + data.y_dir**2
        if dir_mag_sq > 1.0:
            mag = math.sqrt(dir_mag_sq)
            nx, ny = data.x_dir / mag, data.y_dir / mag
        else:
            nx, ny = data.x_dir, data.y_dir
        base_speed = data.movespeed * Consts.GLOBAL_MOVESPEED_TO_USE / 1000.0
        return (nx * base_speed) + data.x_vel, (ny * base_speed) + data.y_vel

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        data = self.get_data(obj_id)
        dt = current_time - data.timestamp
        vx, vy = self.get_velocity(data)
        return data.x_pos + (vx * dt), data.y_pos + (vy * dt)

    def _bake_position(self, obj_id: int, current_time: int) -> None:
        data = self.get_data(obj_id)
        dt = current_time - data.timestamp
        vx, vy = self.get_velocity(data)
        data.x_pos += vx * dt
        data.y_pos += vy * dt
        data.timestamp = current_time

    def _get_target_vector(self, source_id: int, target_id: int, timestamp: int) -> tuple[bool, float, float, float, float, float]:
        if source_id not in self._data_dct or target_id not in self._data_dct:
            return False, 0.0, 0.0, 0.0, 0.0, 0.0
        tar_x, tar_y = self.get_position(target_id, timestamp)
        src_x, src_y = self.get_position(source_id, timestamp)
        dx, dy = tar_x - src_x, tar_y - src_y
        dist = math.hypot(dx, dy)
        return True, dx, dy, dist, tar_x, tar_y

    def _is_within_range(self, current_time: int, source_id: int, target_id: int, range_limit: float) -> bool:
        if range_limit <= 0.0: return True
        valid, _, _, dist, _, _ = self._get_target_vector(source_id, target_id, current_time)
        return valid and dist <= range_limit

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case MovementValidation.IS_TARGET_THE_DESTINATION:
                return self.get_data(source_id).destination_id == target_id
            case MovementValidation.IS_WITHIN_RANGE_OF_DESTINATION:
                return self._is_within_range(timestamp, source_id, self.get_data(source_id).destination_id, validation_value)
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> None:
        match effect_type:
            case MovementEffect.WALK_FORWARD:
                if bool(effect_value) is True:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).y_dir = max(-1.0, min(1.0, self.get_data(obj_id).y_dir + 1.0))
                else:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).y_dir = max(-1.0, min(1.0, self.get_data(obj_id).y_dir - 1.0))
            case MovementEffect.WALK_BACKWARD:
                if bool(effect_value) is True:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).y_dir = max(-1.0, min(1.0, self.get_data(obj_id).y_dir - 1.0))
                else:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).y_dir = max(-1.0, min(1.0, self.get_data(obj_id).y_dir + 1.0))
            case MovementEffect.WALK_LEFT:
                if bool(effect_value) is True:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).x_dir = max(-1.0, min(1.0, self.get_data(obj_id).x_dir - 1.0))
                else:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).x_dir = max(-1.0, min(1.0, self.get_data(obj_id).x_dir + 1.0))
            case MovementEffect.WALK_RIGHT:
                if bool(effect_value) is True:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).x_dir = max(-1.0, min(1.0, self.get_data(obj_id).x_dir + 1.0))
                else:
                    self._bake_position(obj_id, timestamp)
                    self.get_data(obj_id).x_dir = max(-1.0, min(1.0, self.get_data(obj_id).x_dir - 1.0))
            case MovementEffect.WALK_TOWARDS_TARGET:
                data = self.get_data(obj_id)
                valid, dx, dy, dist, _, _ = self._get_target_vector(obj_id, data.destination_id, timestamp)
                if valid and dist > 0.0:
                    self._bake_position(obj_id, timestamp)
                    data.x_dir = dx / dist
                    data.y_dir = dy / dist
            case MovementEffect.STOP_WALK_TOWARDS_TARGET:
                self._bake_position(obj_id, timestamp)
                self.get_data(obj_id).x_dir, self.get_data(obj_id).y_dir = 0.0, 0.0
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
                    target_data = self.get_data(obj_id)
                    speed_per_ms = effect_value * Consts.GLOBAL_MOVESPEED_TO_USE / 1000.0
                    target_data.x_vel = (dx / dist) * speed_per_ms
                    target_data.y_vel = (dy / dist) * speed_per_ms
            case MovementEffect.X_OFFSET:
                self._bake_position(obj_id, timestamp)
                data = self.get_data(obj_id)
                if data.parent_id in self._data_dct:
                    p_x, _ = self.get_position(data.parent_id, timestamp)
                    data.x_pos = p_x
                data.x_pos += effect_value
            case MovementEffect.Y_OFFSET:
                self._bake_position(obj_id, timestamp)
                data = self.get_data(obj_id)
                if data.parent_id in self._data_dct:
                    _, p_y = self.get_position(data.parent_id, timestamp)
                    data.y_pos = p_y
                data.y_pos += effect_value
            case MovementEffect.MOVESPEED:
                self._bake_position(obj_id, timestamp)
                self.get_data(obj_id).movespeed = effect_value