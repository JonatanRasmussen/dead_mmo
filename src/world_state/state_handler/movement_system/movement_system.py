import math
from dataclasses import dataclass
from typing import Dict, Tuple
from src.settings import Consts

@dataclass(slots=True)
class ObjMovementData:
    x_pos: float
    y_pos: float
    x_vel: float
    y_vel: float
    x_dir: float
    y_dir: float
    timestamp: int
    movespeed: float = 1.0

    @classmethod
    def create_environment(cls) -> 'ObjMovementData':
        return cls(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 1.0)

    @classmethod
    def create_spawned(cls, timestamp: int, parent_x: float, parent_y: float) -> 'ObjMovementData':
        return cls(float(parent_x), float(parent_y), 0.0, 0.0, 0.0, 0.0, timestamp, 1.0)

class MovementSystem:
    GLOBAL_MOVESPEED_TO_USE = Consts.MOVEMENT_DISTANCE_PER_SECOND
    MS_PER_MOVEMENT_TICK: float = 1000.0 / Consts.MOVEMENT_UPDATES_PER_SECOND

    def __init__(self) -> None:
        self.game_obj_data_dct: Dict[int, ObjMovementData] = {}

    @classmethod
    def get_velocity(cls, data: ObjMovementData) -> Tuple[float, float]:
        dir_mag_sq = data.x_dir**2 + data.y_dir**2
        if dir_mag_sq > 1.0:
            mag = math.sqrt(dir_mag_sq)
            nx, ny = data.x_dir / mag, data.y_dir / mag
        else:
            nx, ny = data.x_dir, data.y_dir

        base_speed = data.movespeed * cls.GLOBAL_MOVESPEED_TO_USE / 1000.0
        return (nx * base_speed) + data.x_vel, (ny * base_speed) + data.y_vel

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjMovementData.create_environment()

    def spawn_game_obj(self, timestamp: int, parent_obj_id: int, spawned_obj_id: int) -> None:
        if spawned_obj_id in self.game_obj_data_dct: return
        parent_x, parent_y = self.get_position(parent_obj_id, timestamp)
        self.game_obj_data_dct[spawned_obj_id] = ObjMovementData.create_spawned(timestamp, parent_x, parent_y)

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        if obj_id not in self.game_obj_data_dct:
            raise ValueError(f"Object {obj_id} not found in MovementSystem.")
        data = self.game_obj_data_dct[obj_id]
        dt = current_time - data.timestamp
        vx, vy = self.get_velocity(data)
        return data.x_pos + (vx * dt), data.y_pos + (vy * dt)

    def _bake_position(self, obj_id: int, current_time: int) -> None:
        data = self.game_obj_data_dct[obj_id]
        dt = current_time - data.timestamp
        vx, vy = self.get_velocity(data)
        data.x_pos += vx * dt
        data.y_pos += vy * dt
        data.timestamp = current_time

    # ---- State Update Handlers ----

    def walk_forward(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.y_dir = max(-1.0, min(1.0, data.y_dir + 1.0))

    def stop_walk_forward(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.y_dir = max(-1.0, min(1.0, data.y_dir - 1.0))

    def walk_backward(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.y_dir = max(-1.0, min(1.0, data.y_dir - 1.0))

    def stop_walk_backward(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.y_dir = max(-1.0, min(1.0, data.y_dir + 1.0))

    def walk_left(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.x_dir = max(-1.0, min(1.0, data.x_dir - 1.0))

    def stop_walk_left(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.x_dir = max(-1.0, min(1.0, data.x_dir + 1.0))

    def walk_right(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.x_dir = max(-1.0, min(1.0, data.x_dir + 1.0))

    def stop_walk_right(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.x_dir = max(-1.0, min(1.0, data.x_dir - 1.0))

    def walk_source_towards_target(self, source_id: int, target_id: int, timestamp: int):
        if source_id not in self.game_obj_data_dct or target_id not in self.game_obj_data_dct: return
        tar_x, tar_y = self.get_position(target_id, timestamp)
        src_x, src_y = self.get_position(source_id, timestamp)
        dx, dy = tar_x - src_x, tar_y - src_y
        dist = math.hypot(dx, dy)
        self._bake_position(source_id, timestamp)
        if dist > 0.0:
            self.game_obj_data_dct[source_id].x_dir = dx / dist
            self.game_obj_data_dct[source_id].y_dir = dy / dist

    def stop_walk_source_towards_target(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.x_dir, data.y_dir = 0.0, 0.0

    def teleport_source_to_target(self, source_id: int, target_id: int, timestamp: int):
        if source_id not in self.game_obj_data_dct or target_id not in self.game_obj_data_dct: return
        tar_x, tar_y = self.get_position(target_id, timestamp)
        data = self.game_obj_data_dct[source_id]
        data.x_pos, data.y_pos = tar_x, tar_y
        data.x_vel, data.y_vel, data.x_dir, data.y_dir = 0.0, 0.0, 0.0, 0.0
        data.timestamp = timestamp

    def despawn_self(self, source_id: int, timestamp: int):
        if data := self.game_obj_data_dct.get(source_id):
            self._bake_position(source_id, timestamp)
            data.x_dir, data.y_dir, data.x_vel, data.y_vel = 0.0, 0.0, 0.0, 0.0

    def push_target_away_from_source(self, source_id: int, target_id: int, force: float, timestamp: int):
        if source_id not in self.game_obj_data_dct or target_id not in self.game_obj_data_dct: return
        tar_x, tar_y = self.get_position(target_id, timestamp)
        src_x, src_y = self.get_position(source_id, timestamp)
        dx, dy = tar_x - src_x, tar_y - src_y
        dist = math.hypot(dx, dy)
        if dist > 0.0:
            self._bake_position(target_id, timestamp)
            target_data = self.game_obj_data_dct[target_id]
            speed_per_ms = force * self.GLOBAL_MOVESPEED_TO_USE / 1000.0
            target_data.x_vel = (dx / dist) * speed_per_ms
            target_data.y_vel = (dy / dist) * speed_per_ms

    # ---- Utilities ----

    def is_within_range(self, current_time: int, source_id: int, target_id: int, range_limit: float) -> bool:
        if range_limit <= 0.0: return True
        if source_id not in self.game_obj_data_dct or target_id not in self.game_obj_data_dct: return False
        source_x, source_y = self.get_position(source_id, current_time)
        target_x, target_y = self.get_position(target_id, current_time)
        return (source_x - target_x)**2 + (source_y - target_y)**2 <= range_limit**2

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if effect_type == "walk_forward": self.walk_forward(source_id, timestamp)
        elif effect_type == "stop_walk_forward": self.stop_walk_forward(source_id, timestamp)
        elif effect_type == "walk_backward": self.walk_backward(source_id, timestamp)
        elif effect_type == "stop_walk_backward": self.stop_walk_backward(source_id, timestamp)
        elif effect_type == "walk_left": self.walk_left(source_id, timestamp)
        elif effect_type == "stop_walk_left": self.stop_walk_left(source_id, timestamp)
        elif effect_type == "walk_right": self.walk_right(source_id, timestamp)
        elif effect_type == "stop_walk_right": self.stop_walk_right(source_id, timestamp)
        elif effect_type == "walk_towards_target": self.walk_source_towards_target(source_id, target_id, timestamp)
        elif effect_type == "stop_walk_towards_target": self.stop_walk_source_towards_target(source_id, timestamp)
        elif effect_type == "teleport_to_target": self.teleport_source_to_target(source_id, target_id, timestamp)
        elif effect_type == "push_target": self.push_target_away_from_source(source_id, target_id, effect_value, timestamp)
        elif effect_type == "despawn_self": self.despawn_self(source_id, timestamp)
        elif effect_type == "x_offset":
            if data := self.game_obj_data_dct.get(source_id):
                self._bake_position(source_id, timestamp)
                data.x_pos += effect_value
        elif effect_type == "y_offset":
            if data := self.game_obj_data_dct.get(source_id):
                self._bake_position(source_id, timestamp)
                data.y_pos += effect_value
        elif effect_type == "movespeed":
            if data := self.game_obj_data_dct.get(source_id):
                self._bake_position(source_id, timestamp)
                data.movespeed = effect_value