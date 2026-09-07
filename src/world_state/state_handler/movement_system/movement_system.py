import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum, auto

from src.settings import Consts
# Assuming Behavior is importable from your project structure (e.g., src.world_state.behavior)


class MovementBehavior(Enum):
    """ Enumeration of distinct spell movement behaviors. """
    NONE = 0

    # --- INTENT-BASED (WASD MOVEMENT) ---
    WALK_FORWARD = auto()
    WALK_LEFT = auto()
    WALK_BACKWARD = auto()
    WALK_RIGHT = auto()
    STOP_WALK_FORWARD = auto()
    STOP_WALK_LEFT = auto()
    STOP_WALK_BACKWARD = auto()
    STOP_WALK_RIGHT = auto()

    # --- INTENT-BASED (TARGETING) ---
    WALK_SOURCE_TOWARDS_TARGET = auto()
    STOP_WALK_SOURCE_TOWARDS_TARGET = auto()

    # --- INSTANT / UTILITY ---
    TELEPORT_SOURCE_TO_TARGET = auto()
    DESPAWN_SELF = auto()

    # --- PHYSICS-BASED (FORCES) ---
    PUSH_TARGET_AWAY_FROM_SOURCE = auto()


@dataclass(slots=True)
class SpellMovementData:
    """Stores only the movement-relevant data extracted from a Spell."""
    movement_force: float
    range_limit: float
    behavior: MovementBehavior
    spawned_x_offset: float
    spawned_y_offset: float
    spawned_movespeed: float


@dataclass(slots=True)
class ObjMovementData:
    """ECS-style component storing positional and dead-reckoning data for a GameObj."""
    x_pos: float
    y_pos: float

    # PHYSICS (External forces like knockbacks, sliding)
    x_vel: float
    y_vel: float

    # INTENT (WASD or Walk commands)
    x_dir: float
    y_dir: float

    timestamp: int
    movespeed: float = 1.0

    @classmethod
    def create_environment(cls) -> 'ObjMovementData':
        return cls(
            x_pos=0.0,
            y_pos=0.0,
            x_vel=0.0,
            y_vel=0.0,
            x_dir=0.0,
            y_dir=0.0,
            timestamp=0,
            movespeed=1.0,
        )

    @classmethod
    def create_from_spell(cls, timestamp: int, parent_x: float, parent_y: float, spell_data: SpellMovementData) -> 'ObjMovementData':
        return cls(
            x_pos=float(parent_x + spell_data.spawned_x_offset),
            y_pos=float(parent_y + spell_data.spawned_y_offset),
            x_vel=0.0,
            y_vel=0.0,
            x_dir=0.0,
            y_dir=0.0,
            timestamp=timestamp,
            movespeed=spell_data.spawned_movespeed,
        )


class MovementSystem:
    """
    Manages all movement-related logic, geometry, and hitboxes using a dead reckoning design.
    """
    GLOBAL_MOVESPEED_TO_USE = Consts.MOVEMENT_DISTANCE_PER_SECOND
    MS_PER_MOVEMENT_TICK: float = 1000.0 / Consts.MOVEMENT_UPDATES_PER_SECOND

    def __init__(self, spell_data_dct: Dict[int, SpellMovementData]) -> None:
        self.spell_data_dct: Dict[int, SpellMovementData] = spell_data_dct
        self.game_obj_data_dct: Dict[int, ObjMovementData] = {}

    @classmethod
    def get_velocity(cls, data: ObjMovementData) -> Tuple[float, float]:
        """Calculates the combined effective velocity (Intent + Physics)."""
        # Normalize Intent vector so moving diagonally isn't faster
        dir_mag_sq = data.x_dir**2 + data.y_dir**2
        if dir_mag_sq > 1.0:
            mag = math.sqrt(dir_mag_sq)
            nx = data.x_dir / mag
            ny = data.y_dir / mag
        else:
            nx = data.x_dir
            ny = data.y_dir

        # Calculate intent velocity
        base_speed = data.movespeed * cls.GLOBAL_MOVESPEED_TO_USE / 1000.0
        intent_vx = nx * base_speed
        intent_vy = ny * base_speed

        # Combine with physical external forces
        return intent_vx + data.x_vel, intent_vy + data.y_vel

    @classmethod
    def extrapolate(cls, data: 'ObjMovementData', current_time: int | float) -> Tuple[float, float]:
        dt = current_time - data.timestamp
        assert dt >= 0, f"time went backwards ({current_time} < {data.timestamp})"
        eff_dt = float(dt)

        vx, vy = cls.get_velocity(data)
        return data.x_pos + (vx * eff_dt), data.y_pos + (vy * eff_dt)

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjMovementData.create_environment()

    def spawn_game_obj(self, timestamp: int, parent_obj_id: int, spawned_obj_id: int, spell_id: int) -> None:
        if spell_id not in self.spell_data_dct or spawned_obj_id in self.game_obj_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        parent_x_pos, parent_y_pos = self.get_position(parent_obj_id, timestamp)
        self.game_obj_data_dct[spawned_obj_id] = ObjMovementData.create_from_spell(
            timestamp, parent_x_pos, parent_y_pos, spell_data
        )

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        if obj_id not in self.game_obj_data_dct:
            raise ValueError(f"Object {obj_id} not found in MovementSystem.")

        data = self.game_obj_data_dct[obj_id]
        dt = current_time - data.timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards ({current_time} < {data.timestamp})"

        vx, vy = self.get_velocity(data)
        return data.x_pos + (vx * dt), data.y_pos + (vy * dt)

    def _bake_position(self, obj_id: int, current_time: int) -> None:
        """Bakes the current velocity into the base position and updates the timestamp."""
        data = self.game_obj_data_dct[obj_id]
        dt = current_time - data.timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards ({current_time} < {data.timestamp})"

        vx, vy = self.get_velocity(data)
        data.x_pos += vx * dt
        data.y_pos += vy * dt
        data.timestamp = current_time

    def teleport(self, obj_id: int, x: float, y: float, current_time: int) -> None:
        if obj_id not in self.game_obj_data_dct:
            return

        data = self.game_obj_data_dct[obj_id]
        data.x_pos = x
        data.y_pos = y
        # Reset physics and intent completely
        data.x_vel = 0.0
        data.y_vel = 0.0
        data.x_dir = 0.0
        data.y_dir = 0.0
        data.timestamp = current_time


    def apply_movement_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        behavior = spell_data.behavior

        # --- SOURCE-BASED EFFECTS ---
        if behavior in (
            MovementBehavior.WALK_SOURCE_TOWARDS_TARGET,
            MovementBehavior.STOP_WALK_SOURCE_TOWARDS_TARGET,
            MovementBehavior.TELEPORT_SOURCE_TO_TARGET,
            MovementBehavior.DESPAWN_SELF
        ):
            if source_id not in self.game_obj_data_dct:
                return

            source_data = self.game_obj_data_dct[source_id]

            if behavior == MovementBehavior.WALK_SOURCE_TOWARDS_TARGET and target_id in self.game_obj_data_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                src_x, src_y = self.get_position(source_id, timestamp)
                dx = tar_x - src_x
                dy = tar_y - src_y
                dist = math.hypot(dx, dy)

                self._bake_position(source_id, timestamp)
                if dist > 0.0:
                    source_data.x_dir = dx / dist
                    source_data.y_dir = dy / dist

            elif behavior == MovementBehavior.STOP_WALK_SOURCE_TOWARDS_TARGET:
                self._bake_position(source_id, timestamp)
                source_data.x_dir = 0.0
                source_data.y_dir = 0.0

            elif behavior == MovementBehavior.TELEPORT_SOURCE_TO_TARGET and target_id in self.game_obj_data_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                self.teleport(source_id, tar_x, tar_y, timestamp)

            elif behavior == MovementBehavior.DESPAWN_SELF:
                self._bake_position(source_id, timestamp)
                source_data.x_dir = 0.0
                source_data.y_dir = 0.0
                source_data.x_vel = 0.0
                source_data.y_vel = 0.0

        # --- TARGET-BASED EFFECTS (WASD Input) ---
        elif behavior in (
            MovementBehavior.WALK_FORWARD, MovementBehavior.STOP_WALK_FORWARD,
            MovementBehavior.WALK_LEFT, MovementBehavior.STOP_WALK_LEFT,
            MovementBehavior.WALK_BACKWARD, MovementBehavior.STOP_WALK_BACKWARD,
            MovementBehavior.WALK_RIGHT, MovementBehavior.STOP_WALK_RIGHT,
        ):
            if source_id not in self.game_obj_data_dct:
                return

            self._bake_position(source_id, timestamp)
            source_data = self.game_obj_data_dct[source_id]

            if behavior == MovementBehavior.WALK_RIGHT:
                source_data.x_dir += 1.0
            elif behavior == MovementBehavior.STOP_WALK_RIGHT:
                source_data.x_dir -= 1.0
            elif behavior == MovementBehavior.WALK_LEFT:
                source_data.x_dir -= 1.0
            elif behavior == MovementBehavior.STOP_WALK_LEFT:
                source_data.x_dir += 1.0
            elif behavior == MovementBehavior.WALK_FORWARD:
                source_data.y_dir += 1.0
            elif behavior == MovementBehavior.STOP_WALK_FORWARD:
                source_data.y_dir -= 1.0
            elif behavior == MovementBehavior.WALK_BACKWARD:
                source_data.y_dir -= 1.0
            elif behavior == MovementBehavior.STOP_WALK_BACKWARD:
                source_data.y_dir += 1.0

            # Clamp to prevent drift from duplicate events
            source_data.x_dir = max(-1.0, min(1.0, source_data.x_dir))
            source_data.y_dir = max(-1.0, min(1.0, source_data.y_dir))

        # --- PHYSICS EFFECTS (Forces) ---
        elif behavior == MovementBehavior.PUSH_TARGET_AWAY_FROM_SOURCE:
            if source_id not in self.game_obj_data_dct or target_id not in self.game_obj_data_dct:
                return

            tar_x, tar_y = self.get_position(target_id, timestamp)
            src_x, src_y = self.get_position(source_id, timestamp)
            dx = tar_x - src_x
            dy = tar_y - src_y
            dist = math.hypot(dx, dy)

            if dist > 0.0:
                self._bake_position(target_id, timestamp)
                target_data = self.game_obj_data_dct[target_id]

                # Apply as raw velocity (Physics force)
                speed_per_ms = spell_data.movement_force * MovementSystem.GLOBAL_MOVESPEED_TO_USE / 1000.0
                target_data.x_vel = (dx / dist) * speed_per_ms
                target_data.y_vel = (dy / dist) * speed_per_ms

    def get_objects_in_range(self, origin_obj_id: int, range_limit: float, current_time: int) -> List[int]:
        # (Unchanged from original)
        if origin_obj_id not in self.game_obj_data_dct:
            return []

        origin_x, origin_y = self.get_position(origin_obj_id, current_time)
        range_sq = range_limit * range_limit
        objects_in_range = []

        for obj_id in self.game_obj_data_dct:
            if obj_id == origin_obj_id:
                continue

            x, y = self.get_position(obj_id, current_time)
            dist_sq = (x - origin_x) ** 2 + (y - origin_y) ** 2

            if dist_sq <= range_sq:
                objects_in_range.append(obj_id)

        return objects_in_range

    def is_within_range(self,  current_time: int, source_id: int, spell_id: int, target_id: int) -> bool:
        # (Unchanged from original)
        spell_data = self.spell_data_dct[spell_id]
        range_limit = spell_data.range_limit
        if range_limit <= 0.0:
            return True
        if (source_id not in self.game_obj_data_dct or target_id not in self.game_obj_data_dct):
            return False
        source_x, source_y = self.get_position(source_id, current_time)
        target_x, target_y = self.get_position(target_id, current_time)
        dx = source_x - target_x
        dy = source_y - target_y
        return dx * dx + dy * dy <= range_limit * range_limit

    def check_collision(self, obj_id_1: int, obj_id_2: int, current_time: int, range_limit: float) -> bool:
        # (Unchanged from original)
        if obj_id_1 not in self.game_obj_data_dct or obj_id_2 not in self.game_obj_data_dct:
            return False

        x1, y1 = self.get_position(obj_id_1, current_time)
        x2, y2 = self.get_position(obj_id_2, current_time)

        dist_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        collision_distance_sq = range_limit ** 2

        return dist_sq <= collision_distance_sq