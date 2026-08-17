import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import IntFlag, auto

from src.settings import Consts
from ._spell_database import SpellDatabase
from src.world_state import Behavior
# Assuming Behavior is importable from your project structure (e.g., src.world_state.behavior)


class MovementBehavior(IntFlag):
    """ Various bitflags that define spell behavior. """
    NONE = 0

    # MOVEMENT
    MOVE_UP = auto()
    MOVE_LEFT = auto()
    MOVE_DOWN = auto()
    MOVE_RIGHT = auto()
    STOP_MOVE_UP = auto()
    STOP_MOVE_LEFT = auto()
    STOP_MOVE_DOWN = auto()
    STOP_MOVE_RIGHT = auto()

    MOVE_TOWARDS_TARGET = auto()
    STOP_MOVE_TOWARDS_TARGET = auto()

    TELEPORT_TO_TARGET = auto()
    FORCE_MOVE = auto()
    TRY_MOVE = auto()
    DESPAWN_SELF = auto()

    @classmethod
    def from_behavior(cls, behavior: Behavior) -> "MovementBehavior":
        """Extract the movement-related flags from a Behavior."""
        result = cls.NONE
        for flag in cls:
            if flag is not cls.NONE and flag.name is not None and behavior & getattr(Behavior, flag.name):
                result |= flag
        return result


@dataclass(slots=True)
class SpellMovementData:
    """Stores only the movement-relevant data extracted from a Spell."""
    power: float
    range_limit: float
    cast_time: int
    flags: MovementBehavior
    spawned_x_offset: float
    spawned_y_offset: float
    spawned_movespeed: float


@dataclass(slots=True)
class ObjMovementData:
    """ECS-style component storing positional and dead-reckoning data for a GameObj.

    The X and Y axes are fully independent: each has its own base position,
    velocity and timestamp. An event that only concerns the X axis must never
    read or write any of the Y fields (and vice versa). This should be changed
    in the future, but for now we need it like this to be identical in behavior
    to the old movement system that relied on aura event ticks unique for x and y.
    """
    x_pos: float
    y_pos: float
    x_vel: float
    y_vel: float
    x_timestamp: int
    y_timestamp: int
    movespeed: float = 1.0


class MovementSystem:
    """
    Manages all movement-related logic, geometry, and hitboxes using a dead reckoning design.
    Positional data is calculated via time-deltas rather than per-frame updates.
    """

    GLOBAL_MOVESPEED_TO_USE = Consts.MOVEMENT_DISTANCE_PER_SECOND

    # --- FEATURE FLAG ---
    CONSTRAIN_TO_TICK_RATE: bool = True
    MS_PER_MOVEMENT_TICK: float = 1000.0 / Consts.MOVEMENT_UPDATES_PER_SECOND

    def __init__(self, spell_database: SpellDatabase) -> None:
        # Maps spell_id -> SpellMovementData
        self.spell_data_dct: Dict[int, SpellMovementData] = MovementSystem._create_initialized_spell_data_dct(spell_database)
        # Maps obj_id -> MovementData
        self.game_obj_positions_dct: Dict[int, ObjMovementData] = {}

    @classmethod
    def extrapolate(cls, data: 'ObjMovementData', current_time: int | float) -> Tuple[float, float]:
        """Pure dead-reckoning read of an ObjMovementData. Single source of truth
        for the quantisation, shared by get_position and the debug harness."""
        x_dt = current_time - data.x_timestamp
        y_dt = current_time - data.y_timestamp
        assert x_dt >= 0, f"time went backwards on X ({current_time} < {data.x_timestamp})"
        assert y_dt >= 0, f"time went backwards on Y ({current_time} < {data.y_timestamp})"
        if cls.CONSTRAIN_TO_TICK_RATE:
            eff_x = math.floor(x_dt / cls.MS_PER_MOVEMENT_TICK) * cls.MS_PER_MOVEMENT_TICK
            eff_y = math.floor(y_dt / cls.MS_PER_MOVEMENT_TICK) * cls.MS_PER_MOVEMENT_TICK
        else:
            eff_x, eff_y = float(x_dt), float(y_dt)
        return data.x_pos + data.x_vel * eff_x, data.y_pos + data.y_vel * eff_y

    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> Dict[int, SpellMovementData]:
        """
        Loads movement-relevant data from a SpellDatabase into memory.
        The Spell object itself is discarded after extraction.
        """
        spell_data_dct = {}
        for spell in spell_database.get_all_spells():
            spell_data_dct[spell.spell_id] = SpellMovementData(
            flags=MovementBehavior.from_behavior(spell.flags),
            power=spell.power,
            range_limit=spell.range_limit,
            cast_time=spell.cast_time,
            spawned_x_offset=spell.get_spawned_obj_pos_xy_speed[0],
            spawned_y_offset=spell.get_spawned_obj_pos_xy_speed[1],
            spawned_movespeed=spell.get_spawned_obj_movespeed,
        )
        return spell_data_dct

    def create_environment_obj(self, obj_id: int) -> None:
        """
        Creates the base environment object.
        As the first object created, it bypasses parent positional lookups and spawns at origin.
        """
        self.game_obj_positions_dct[obj_id] = ObjMovementData(
            x_pos=0.0,
            y_pos=0.0,
            x_vel=0.0,
            y_vel=0.0,
            x_timestamp=0,  # Safe to use 0 since velocity is 0 (dt won't affect position)
            y_timestamp=0,
            movespeed=1.0   # Environment is stationary
        )

    def spawn_game_obj(self, timestamp: int, parent_obj_id: int, spawned_obj_id: int, spell_id: int) -> None:
        """Registers a GameObj into the movement system, extracting its initial state."""
        spell_data = self.spell_data_dct[spell_id]
        parent_x_pos, parent_y_pos = self.get_position(parent_obj_id, timestamp)
        self.game_obj_positions_dct[spawned_obj_id] = ObjMovementData(
            x_pos=float(parent_x_pos + spell_data.spawned_x_offset),
            y_pos=float(parent_y_pos + spell_data.spawned_y_offset),
            x_vel=0.0,
            y_vel=0.0,
            x_timestamp=timestamp,
            y_timestamp=timestamp,
            movespeed=spell_data.spawned_movespeed,
        )

    def despawn_game_obj(self, obj_id: int) -> None:
        """Removes an object from the movement system (e.g., on despawn)."""
        self.game_obj_positions_dct.pop(obj_id, None)

    def _effective_dt(self, dt: int) -> float:
        """
        Converts a raw millisecond delta into the delta that has actually been
        'paid out' as movement.

        With CONSTRAIN_TO_TICK_RATE the object only moves on aura ticks, and the
        aura fires once immediately on application, so the number of ticks that
        have fired in [start, start + dt] is floor(dt / tick) + 1.
        """
        if not self.CONSTRAIN_TO_TICK_RATE:
            return float(dt)
        return (math.floor(dt / self.MS_PER_MOVEMENT_TICK) + 0) * self.MS_PER_MOVEMENT_TICK

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        """Calculates the current (x, y) position of an object using dead reckoning."""
        if obj_id not in self.game_obj_positions_dct:
            raise ValueError(f"Object {obj_id} not found in MovementSystem.")

        data = self.game_obj_positions_dct[obj_id]

        # 1 timestamp unit = 1 ms. Events are guaranteed in order; going backwards is a bug.
        x_dt = current_time - data.x_timestamp
        y_dt = current_time - data.y_timestamp
        assert x_dt >= 0, f"Obj {obj_id}: time went backwards on X ({current_time} < {data.x_timestamp})"
        assert y_dt >= 0, f"Obj {obj_id}: time went backwards on Y ({current_time} < {data.y_timestamp})"

        # Velocity is stored in units per millisecond
        current_x = data.x_pos + (data.x_vel * self._effective_dt(x_dt))
        current_y = data.y_pos + (data.y_vel * self._effective_dt(y_dt))

        return current_x, current_y

    def _update_x_base_position(self, obj_id: int, current_time: int) -> None:
        """Bakes the current X velocity into the base X position and updates the X timestamp."""
        data = self.game_obj_positions_dct[obj_id]
        dt = current_time - data.x_timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards on X ({current_time} < {data.x_timestamp})"
        data.x_pos += data.x_vel * self._effective_dt(dt)
        data.x_timestamp = current_time

    def _update_y_base_position(self, obj_id: int, current_time: int) -> None:
        """Bakes the current Y velocity into the base Y position and updates the Y timestamp."""
        data = self.game_obj_positions_dct[obj_id]
        dt = current_time - data.y_timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards on Y ({current_time} < {data.y_timestamp})"
        data.y_pos += data.y_vel * self._effective_dt(dt)
        data.y_timestamp = current_time

    def set_x_velocity(self, obj_id: int, vx: float, current_time: int) -> None:
        """Updates ONLY the X velocity. The Y axis is left completely untouched."""
        if obj_id not in self.game_obj_positions_dct:
            return

        self._update_x_base_position(obj_id, current_time)
        self.game_obj_positions_dct[obj_id].x_vel = vx

    def set_y_velocity(self, obj_id: int, vy: float, current_time: int) -> None:
        """Updates ONLY the Y velocity. The X axis is left completely untouched."""
        if obj_id not in self.game_obj_positions_dct:
            return

        self._update_y_base_position(obj_id, current_time)
        self.game_obj_positions_dct[obj_id].y_vel = vy

    def set_velocity(self, obj_id: int, vx: float, vy: float, current_time: int) -> None:
        """Updates both velocities at once (for movement that is inherently 2D)."""
        self.set_x_velocity(obj_id, vx, current_time)
        self.set_y_velocity(obj_id, vy, current_time)

    def teleport(self, obj_id: int, x: float, y: float, current_time: int) -> None:
        """Instantly moves an object to a new position, halting its velocity."""
        if obj_id not in self.game_obj_positions_dct:
            return

        data = self.game_obj_positions_dct[obj_id]
        data.x_pos = x
        data.y_pos = y
        data.x_vel = 0.0
        data.y_vel = 0.0
        data.x_timestamp = current_time
        data.y_timestamp = current_time

    def apply_movement_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        """
        Applies a spell's movement behavior using dynamic bitflags.
        """
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags

        # Apply Source Effects (Move Towards, Teleport)
        if source_id in self.game_obj_positions_dct:
            source_data = self.game_obj_positions_dct[source_id]
            speed_per_ms = (source_data.movespeed * spell_data.power) * MovementSystem.GLOBAL_MOVESPEED_TO_USE / 1000.0

            if flags & MovementBehavior.MOVE_TOWARDS_TARGET and target_id in self.game_obj_positions_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                src_x, src_y = self.get_position(source_id, timestamp)
                dx = tar_x - src_x
                dy = tar_y - src_y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    vx = (dx / dist) * speed_per_ms
                    vy = (dy / dist) * speed_per_ms
                    self.set_velocity(source_id, vx, vy, timestamp)
                return

            if flags & MovementBehavior.STOP_MOVE_TOWARDS_TARGET:
                self.set_velocity(source_id, 0.0, 0.0, timestamp)
                return

            if flags & MovementBehavior.TELEPORT_TO_TARGET and target_id in self.game_obj_positions_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                self.teleport(source_id, tar_x, tar_y, timestamp)
                return

            if flags & MovementBehavior.DESPAWN_SELF:
                self.set_velocity(source_id, 0.0, 0.0, timestamp)
                return

        # Apply Target Effects (Step Up, Down, Left, Right)
        if target_id in self.game_obj_positions_dct:
            target_data = self.game_obj_positions_dct[target_id]
            speed_per_ms = (target_data.movespeed * spell_data.power) * MovementSystem.GLOBAL_MOVESPEED_TO_USE / 1000.0

            # X Axis Evaluator
            if flags & MovementBehavior.MOVE_RIGHT:
                self.set_x_velocity(target_id, speed_per_ms, timestamp)
            elif flags & MovementBehavior.MOVE_LEFT:
                self.set_x_velocity(target_id, -speed_per_ms, timestamp)
            elif flags & (MovementBehavior.STOP_MOVE_RIGHT | MovementBehavior.STOP_MOVE_LEFT):
                self.set_x_velocity(target_id, 0.0, timestamp)

            # Y Axis Evaluator
            if flags & MovementBehavior.MOVE_UP:
                self.set_y_velocity(target_id, speed_per_ms, timestamp)
            elif flags & MovementBehavior.MOVE_DOWN:
                self.set_y_velocity(target_id, -speed_per_ms, timestamp)
            elif flags & (MovementBehavior.STOP_MOVE_UP | MovementBehavior.STOP_MOVE_DOWN):
                self.set_y_velocity(target_id, 0.0, timestamp)


    def get_objects_in_range(self, origin_obj_id: int, range_limit: float, current_time: int) -> List[int]:
        """Returns a list of obj_ids that are within range_limit of the origin_obj_id."""
        if origin_obj_id not in self.game_obj_positions_dct:
            return []

        origin_x, origin_y = self.get_position(origin_obj_id, current_time)
        range_sq = range_limit * range_limit
        objects_in_range = []

        for obj_id in self.game_obj_positions_dct:
            if obj_id == origin_obj_id:
                continue

            x, y = self.get_position(obj_id, current_time)
            dist_sq = (x - origin_x) ** 2 + (y - origin_y) ** 2

            if dist_sq <= range_sq:
                objects_in_range.append(obj_id)

        return objects_in_range

    def is_within_range(self,  current_time: int, source_id: int, spell_id: int, target_id: int) -> bool:
        """Returns whether two objects are within range of each other."""
        spell_data = self.spell_data_dct[spell_id]
        range_limit = spell_data.range_limit
        if range_limit <= 0.0:
            return True
        if (source_id not in self.game_obj_positions_dct or target_id not in self.game_obj_positions_dct):
            return False
        source_x, source_y = self.get_position(source_id, current_time)
        target_x, target_y = self.get_position(target_id, current_time)
        dx = source_x - target_x
        dy = source_y - target_y
        return dx * dx + dy * dy <= range_limit * range_limit

    def check_collision(self, obj_id_1: int, obj_id_2: int, current_time: int, range_limit: float) -> bool:
        """Checks if two objects' hitboxes are overlapping."""
        if obj_id_1 not in self.game_obj_positions_dct or obj_id_2 not in self.game_obj_positions_dct:
            return False

        x1, y1 = self.get_position(obj_id_1, current_time)
        x2, y2 = self.get_position(obj_id_2, current_time)

        dist_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        collision_distance_sq = range_limit ** 2

        return dist_sq <= collision_distance_sq