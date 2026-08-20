import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import IntFlag, auto

from src.settings import Consts
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


@dataclass(slots=True)
class SpellMovementData:
    """Stores only the movement-relevant data extracted from a Spell."""
    power: float
    range_limit: float
    flags: MovementBehavior
    spawned_x_offset: float
    spawned_y_offset: float
    spawned_movespeed: float


@dataclass(slots=True)
class ObjMovementData:
    """ECS-style component storing positional and dead-reckoning data for a GameObj."""
    x_pos: float
    y_pos: float
    x_vel: float
    y_vel: float
    x_timestamp: int
    y_timestamp: int
    movespeed: float = 1.0

    @classmethod
    def create_environment(cls) -> 'ObjMovementData':
        return cls(
            x_pos=0.0,
            y_pos=0.0,
            x_vel=0.0,
            y_vel=0.0,
            x_timestamp=0,
            y_timestamp=0,
            movespeed=1.0
        )

    @classmethod
    def create_from_spell(cls, timestamp: int, parent_x: float, parent_y: float, spell_data: SpellMovementData) -> 'ObjMovementData':
        return cls(
            x_pos=float(parent_x + spell_data.spawned_x_offset),
            y_pos=float(parent_y + spell_data.spawned_y_offset),
            x_vel=0.0,
            y_vel=0.0,
            x_timestamp=timestamp,
            y_timestamp=timestamp,
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
    def extrapolate(cls, data: 'ObjMovementData', current_time: int | float) -> Tuple[float, float]:
        x_dt = current_time - data.x_timestamp
        y_dt = current_time - data.y_timestamp
        assert x_dt >= 0, f"time went backwards on X ({current_time} < {data.x_timestamp})"
        assert y_dt >= 0, f"time went backwards on Y ({current_time} < {data.y_timestamp})"
        eff_x, eff_y = float(x_dt), float(y_dt)
        return data.x_pos + data.x_vel * eff_x, data.y_pos + data.y_vel * eff_y

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
        """Removes an object from the movement system (e.g., on despawn)."""
        self.game_obj_data_dct.pop(obj_id, None)

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        """Calculates the current (x, y) position of an object using dead reckoning."""
        if obj_id not in self.game_obj_data_dct:
            raise ValueError(f"Object {obj_id} not found in MovementSystem.")

        data = self.game_obj_data_dct[obj_id]

        # 1 timestamp unit = 1 ms. Events are guaranteed in order; going backwards is a bug.
        x_dt = current_time - data.x_timestamp
        y_dt = current_time - data.y_timestamp
        assert x_dt >= 0, f"Obj {obj_id}: time went backwards on X ({current_time} < {data.x_timestamp})"
        assert y_dt >= 0, f"Obj {obj_id}: time went backwards on Y ({current_time} < {data.y_timestamp})"

        # Velocity is stored in units per millisecond
        current_x = data.x_pos + (data.x_vel * x_dt)
        current_y = data.y_pos + (data.y_vel * y_dt)

        return current_x, current_y

    def _update_x_base_position(self, obj_id: int, current_time: int) -> None:
        """Bakes the current X velocity into the base X position and updates the X timestamp."""
        data = self.game_obj_data_dct[obj_id]
        dt = current_time - data.x_timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards on X ({current_time} < {data.x_timestamp})"
        data.x_pos += data.x_vel * dt
        data.x_timestamp = current_time

    def _update_y_base_position(self, obj_id: int, current_time: int) -> None:
        """Bakes the current Y velocity into the base Y position and updates the Y timestamp."""
        data = self.game_obj_data_dct[obj_id]
        dt = current_time - data.y_timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards on Y ({current_time} < {data.y_timestamp})"
        data.y_pos += data.y_vel * dt
        data.y_timestamp = current_time

    def set_x_velocity(self, obj_id: int, vx: float, current_time: int) -> None:
        """Updates ONLY the X velocity. The Y axis is left completely untouched."""
        if obj_id not in self.game_obj_data_dct:
            return

        self._update_x_base_position(obj_id, current_time)
        self.game_obj_data_dct[obj_id].x_vel = vx

    def set_y_velocity(self, obj_id: int, vy: float, current_time: int) -> None:
        """Updates ONLY the Y velocity. The X axis is left completely untouched."""
        if obj_id not in self.game_obj_data_dct:
            return

        self._update_y_base_position(obj_id, current_time)
        self.game_obj_data_dct[obj_id].y_vel = vy

    def set_velocity(self, obj_id: int, vx: float, vy: float, current_time: int) -> None:
        """Updates both velocities at once (for movement that is inherently 2D)."""
        self.set_x_velocity(obj_id, vx, current_time)
        self.set_y_velocity(obj_id, vy, current_time)

    def teleport(self, obj_id: int, x: float, y: float, current_time: int) -> None:
        """Instantly moves an object to a new position, halting its velocity."""
        if obj_id not in self.game_obj_data_dct:
            return

        data = self.game_obj_data_dct[obj_id]
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
        if source_id in self.game_obj_data_dct:
            source_data = self.game_obj_data_dct[source_id]
            speed_per_ms = (source_data.movespeed * spell_data.power) * MovementSystem.GLOBAL_MOVESPEED_TO_USE / 1000.0

            if flags & MovementBehavior.MOVE_TOWARDS_TARGET and target_id in self.game_obj_data_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                src_x, src_y = self.get_position(source_id, timestamp)
                dx = tar_x - src_x
                dy = tar_y - src_y
                dist = math.hypot(dx, dy)
                if dist > 0.0:
                    vx = (dx / dist) * speed_per_ms
                    vy = (dy / dist) * speed_per_ms
                    self.set_velocity(source_id, vx, vy, timestamp)
                return

            if flags & MovementBehavior.STOP_MOVE_TOWARDS_TARGET:
                self.set_velocity(source_id, 0.0, 0.0, timestamp)
                return

            if flags & MovementBehavior.TELEPORT_TO_TARGET and target_id in self.game_obj_data_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                self.teleport(source_id, tar_x, tar_y, timestamp)
                return

            if flags & MovementBehavior.DESPAWN_SELF:
                self.set_velocity(source_id, 0.0, 0.0, timestamp)
                return

        # Apply Target Effects (Step Up, Down, Left, Right)
        if target_id in self.game_obj_data_dct:
            target_data = self.game_obj_data_dct[target_id]
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
        """Returns whether two objects are within range of each other."""
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
        """Checks if two objects' hitboxes are overlapping."""
        if obj_id_1 not in self.game_obj_data_dct or obj_id_2 not in self.game_obj_data_dct:
            return False

        x1, y1 = self.get_position(obj_id_1, current_time)
        x2, y2 = self.get_position(obj_id_2, current_time)

        dist_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        collision_distance_sq = range_limit ** 2

        return dist_sq <= collision_distance_sq


#BROKEN CODE
'''
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import IntFlag, auto

from src.settings import Consts


class MovementBehavior(IntFlag):
    """Various bitflags that define spell behavior."""
    NONE = 0

    # --- WASD-style directional input (key-down / key-up) ---
    MOVE_UP = auto()
    MOVE_LEFT = auto()
    MOVE_DOWN = auto()
    MOVE_RIGHT = auto()
    STOP_MOVE_UP = auto()
    STOP_MOVE_LEFT = auto()
    STOP_MOVE_DOWN = auto()
    STOP_MOVE_RIGHT = auto()

    # --- Generic velocity contributions ---
    APPLY_VELOCITY = auto()
    REMOVE_VELOCITY = auto()

    MOVE_TOWARDS_TARGET = auto()
    STOP_MOVE_TOWARDS_TARGET = auto()

    TELEPORT_TO_TARGET = auto()
    FORCE_MOVE = auto()
    TRY_MOVE = auto()
    DESPAWN_SELF = auto()

    # Scale this contribution by the target's own movespeed stat.
    # Without it, `power` is an absolute rate and the obj's movespeed is ignored
    # (use for knockbacks, conveyor belts, scripted pulls, etc).
    USE_MOVESPEED = auto()


# Convenience masks
_MOVE_KEYS = (
    MovementBehavior.MOVE_UP
    | MovementBehavior.MOVE_LEFT
    | MovementBehavior.MOVE_DOWN
    | MovementBehavior.MOVE_RIGHT
)
_STOP_KEYS = (
    MovementBehavior.STOP_MOVE_UP
    | MovementBehavior.STOP_MOVE_LEFT
    | MovementBehavior.STOP_MOVE_DOWN
    | MovementBehavior.STOP_MOVE_RIGHT
)
_WASD_MASK = _MOVE_KEYS | _STOP_KEYS

# (flag, axis_dx, axis_dy, sign) -- sign is +1 for key-down, -1 for key-up.
# Applying `sign * (dx, dy)` to the current axis value and clamping to [-1, 1]
# fully reproduces the WASD state machine without storing any key bitmask.
_WASD_DELTAS: Tuple[Tuple[MovementBehavior, float, float], ...] = (
    (MovementBehavior.MOVE_UP,         0.0,  1.0),
    (MovementBehavior.MOVE_DOWN,       0.0, -1.0),
    (MovementBehavior.MOVE_LEFT,      -1.0,  0.0),
    (MovementBehavior.MOVE_RIGHT,      1.0,  0.0),
    (MovementBehavior.STOP_MOVE_UP,    0.0, -1.0),
    (MovementBehavior.STOP_MOVE_DOWN,  0.0,  1.0),
    (MovementBehavior.STOP_MOVE_LEFT,  1.0,  0.0),
    (MovementBehavior.STOP_MOVE_RIGHT, -1.0, 0.0),
)


def _clamp_unit(value: float) -> float:
    """Clamps an axis component to [-1.0, 1.0]."""
    if value > 1.0:
        return 1.0
    if value < -1.0:
        return -1.0
    return value


@dataclass(slots=True)
class SpellMovementData:
    """Stores only the movement-relevant data extracted from a Spell."""
    power: float
    range_limit: float
    flags: MovementBehavior
    spawned_x_offset: float
    spawned_y_offset: float
    spawned_movespeed: float


@dataclass(slots=True)
class VelocityContribution:
    """
    A single source's contribution to a target's movement.

    Stored as a *raw axis vector* whose components live in [-1, 1]. For WASD
    this doubles as the key state: (-1, 0) means A is held, (0, 0) means either
    nothing or A+D, and so on. It is deliberately lossy -- see _apply_wasd.

    The contribution is normalised to unit length (then scaled by `power`) at
    read time, so a single source moving diagonally is not sqrt(2) faster than
    one moving cardinally.

    `use_movespeed` records whether the target's movespeed stat multiplies this
    contribution, captured from the spell's USE_MOVESPEED flag at apply time.
    """
    axis_x: float
    axis_y: float
    power: float
    use_movespeed: bool = True


@dataclass(slots=True)
class ObjMovementData:
    """ECS-style component storing positional and dead-reckoning data for a GameObj."""
    x_pos: float
    y_pos: float
    timestamp: int
    movespeed: float = 1.0
    # source_obj_id -> that source's current velocity contribution
    velocities: Dict[int, VelocityContribution] = field(default_factory=dict)

    @classmethod
    def create_environment(cls) -> 'ObjMovementData':
        return cls(x_pos=0.0, y_pos=0.0, timestamp=0, movespeed=1.0)

    @classmethod
    def create_from_spell(
        cls,
        timestamp: int,
        parent_x: float,
        parent_y: float,
        spell_data: SpellMovementData,
    ) -> 'ObjMovementData':
        return cls(
            x_pos=float(parent_x + spell_data.spawned_x_offset),
            y_pos=float(parent_y + spell_data.spawned_y_offset),
            timestamp=timestamp,
            movespeed=spell_data.spawned_movespeed,
        )


class MovementSystem:
    """
    Manages all movement-related logic, geometry, and hitboxes using a dead
    reckoning design.

    Each object holds a dict of active velocity contributions keyed by the
    obj_id of whatever is pushing it. Net velocity is recomputed on demand:
    each source is individually normalised (so diagonals aren't faster), then
    all sources are summed as plain vectors (so stacked effects CAN exceed
    normal movespeed). Positions are always
        base_pos + net_velocity * (now - timestamp)
    and every mutation bakes the base position first.
    """
    GLOBAL_MOVESPEED_TO_USE = Consts.MOVEMENT_DISTANCE_PER_SECOND
    MS_PER_MOVEMENT_TICK: float = 1000.0 / Consts.MOVEMENT_UPDATES_PER_SECOND

    def __init__(self, spell_data_dct: Dict[int, SpellMovementData]) -> None:
        self.spell_data_dct: Dict[int, SpellMovementData] = spell_data_dct
        self.game_obj_data_dct: Dict[int, ObjMovementData] = {}

    # ------------------------------------------------------------------
    # Velocity resolution
    # ------------------------------------------------------------------

    @classmethod
    def _compute_velocity(cls, data: ObjMovementData) -> Tuple[float, float]:
        """
        Resolve the dict of contributions into a single (vx, vy) in units/ms.

        Per-source: normalise to unit length, scale by that source's `power`,
        and multiply by the obj's movespeed only if that contribution was
        flagged USE_MOVESPEED.

        Cross-source: plain vector addition. Two sources each pushing at full
        power in the same direction yield double speed -- this is intentional.
        """
        if not data.velocities:
            return 0.0, 0.0

        sum_x = 0.0
        sum_y = 0.0

        for contrib in data.velocities.values():
            length = math.hypot(contrib.axis_x, contrib.axis_y)
            if length <= 0.0 or contrib.power == 0.0:
                continue

            magnitude = contrib.power
            if contrib.use_movespeed:
                magnitude *= data.movespeed

            scale = magnitude / length
            sum_x += contrib.axis_x * scale
            sum_y += contrib.axis_y * scale

        rate = cls.GLOBAL_MOVESPEED_TO_USE / 1000.0
        return sum_x * rate, sum_y * rate

    def get_velocity(self, obj_id: int) -> Tuple[float, float]:
        """Current net velocity of an object, in units per millisecond."""
        data = self.game_obj_data_dct.get(obj_id)
        if data is None:
            return 0.0, 0.0
        return self._compute_velocity(data)

    @classmethod
    def extrapolate(cls, data: ObjMovementData, current_time: int | float) -> Tuple[float, float]:
        dt = current_time - data.timestamp
        assert dt >= 0, f"time went backwards ({current_time} < {data.timestamp})"
        vx, vy = cls._compute_velocity(data)
        return data.x_pos + vx * dt, data.y_pos + vy * dt

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjMovementData.create_environment()

    def spawn_game_obj(
        self, timestamp: int, parent_obj_id: int, spawned_obj_id: int, spell_id: int
    ) -> None:
        if spell_id not in self.spell_data_dct or spawned_obj_id in self.game_obj_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        parent_x_pos, parent_y_pos = self.get_position(parent_obj_id, timestamp)
        self.game_obj_data_dct[spawned_obj_id] = ObjMovementData.create_from_spell(
            timestamp, parent_x_pos, parent_y_pos, spell_data
        )

    def despawn_game_obj(self, obj_id: int) -> None:
        """Removes an object from the movement system (e.g., on despawn)."""
        self.game_obj_data_dct.pop(obj_id, None)
        # Drop any contributions this object was applying to others, otherwise
        # a dead pusher keeps pushing forever.
        for data in self.game_obj_data_dct.values():
            data.velocities.pop(obj_id, None)

    # ------------------------------------------------------------------
    # Position / base-position bookkeeping
    # ------------------------------------------------------------------

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        """Calculates the current (x, y) position of an object using dead reckoning."""
        data = self.game_obj_data_dct.get(obj_id)
        if data is None:
            raise ValueError(f"Object {obj_id} not found in MovementSystem.")

        # 1 timestamp unit = 1 ms. Events are guaranteed in order; going
        # backwards is a bug.
        dt = current_time - data.timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards ({current_time} < {data.timestamp})"

        vx, vy = self._compute_velocity(data)
        return data.x_pos + vx * dt, data.y_pos + vy * dt

    def _bake_position(self, obj_id: int, current_time: int) -> ObjMovementData:
        """
        Advances the base position to `current_time` and resets the timestamp.
        Must be called before any mutation that changes the net velocity.
        """
        data = self.game_obj_data_dct[obj_id]
        dt = current_time - data.timestamp
        assert dt >= 0, f"Obj {obj_id}: time went backwards ({current_time} < {data.timestamp})"
        if dt:
            vx, vy = self._compute_velocity(data)
            data.x_pos += vx * dt
            data.y_pos += vy * dt
        data.timestamp = current_time
        return data

    def set_movespeed(self, obj_id: int, movespeed: float, current_time: int) -> None:
        """
        Changes an object's movespeed. Bakes first, since USE_MOVESPEED
        contributions are scaled at read time and we must not retroactively
        rescale already-travelled distance.
        """
        if obj_id not in self.game_obj_data_dct:
            return
        data = self._bake_position(obj_id, current_time)
        data.movespeed = movespeed

    # ------------------------------------------------------------------
    # Velocity contribution API
    # ------------------------------------------------------------------

    def apply_velocity(
        self,
        target_id: int,
        source_id: int,
        dir_x: float,
        dir_y: float,
        power: float,
        current_time: int,
        use_movespeed: bool = True,
    ) -> None:
        """
        Adds or replaces `source_id`'s velocity contribution on `target_id`.
        `dir_x`/`dir_y` need not be normalised; only their direction matters,
        magnitude comes from `power`.
        """
        if target_id not in self.game_obj_data_dct:
            return

        data = self._bake_position(target_id, current_time)

        length = math.hypot(dir_x, dir_y)
        if length <= 0.0 or power == 0.0:
            data.velocities.pop(source_id, None)
            return

        data.velocities[source_id] = VelocityContribution(
            axis_x=dir_x / length,
            axis_y=dir_y / length,
            power=power,
            use_movespeed=use_movespeed,
        )

    def remove_velocity(self, target_id: int, source_id: int, current_time: int) -> None:
        """Removes `source_id`'s contribution from `target_id`, if present."""
        data = self.game_obj_data_dct.get(target_id)
        if data is None or source_id not in data.velocities:
            return
        self._bake_position(target_id, current_time)
        data.velocities.pop(source_id, None)

    def clear_velocities(self, target_id: int, current_time: int) -> None:
        """Removes every contribution acting on `target_id`."""
        data = self.game_obj_data_dct.get(target_id)
        if data is None or not data.velocities:
            return
        self._bake_position(target_id, current_time)
        data.velocities.clear()

    def teleport(self, obj_id: int, x: float, y: float, current_time: int) -> None:
        """Instantly moves an object to a new position, halting all velocity."""
        data = self.game_obj_data_dct.get(obj_id)
        if data is None:
            return
        data.x_pos = x
        data.y_pos = y
        data.timestamp = current_time
        data.velocities.clear()

    # ------------------------------------------------------------------
    # WASD handling
    # ------------------------------------------------------------------

    def _apply_wasd(
        self,
        target_id: int,
        source_id: int,
        flags: MovementBehavior,
        power: float,
        current_time: int,
        use_movespeed: bool,
    ) -> None:
        """
        Folds WASD key-down/key-up events into the existing contribution from
        `source_id`, deriving the held-key state from the stored axis vector.

        Each axis component lives in [-1, 1] and IS the key state for that axis:
            -1 -> negative key alone,  +1 -> positive key alone,
             0 -> neither, or both (opposites cancelled).

        A key-down adds the key's direction; a key-up subtracts it. Both are
        clamped to [-1, 1]. Receiving a STOP_MOVE_X is treated as proof that
        MOVE_X was held, so subtracting correctly resumes motion toward the
        still-held opposite key. The clamp makes redundant key-downs (e.g.
        pressing A while already moving left) a no-op rather than double speed,
        and lets a desynced state re-converge once the key is truly released.
        """
        data = self.game_obj_data_dct.get(target_id)
        if data is None:
            return

        existing = data.velocities.get(source_id)
        axis_x = existing.axis_x if existing is not None else 0.0
        axis_y = existing.axis_y if existing is not None else 0.0

        for flag, dx, dy in _WASD_DELTAS:
            if flags & flag:
                axis_x = _clamp_unit(axis_x + dx)
                axis_y = _clamp_unit(axis_y + dy)

        data = self._bake_position(target_id, current_time)

        if axis_x == 0.0 and axis_y == 0.0:
            # Either nothing is held, or opposites cancel. Keep a zero-magnitude
            # record so a later STOP_MOVE can resume toward the opposite key.
            data.velocities[source_id] = VelocityContribution(
                0.0, 0.0, power, use_movespeed
            )
            return

        data.velocities[source_id] = VelocityContribution(
            axis_x=axis_x,
            axis_y=axis_y,
            power=power,
            use_movespeed=use_movespeed,
        )

    # ------------------------------------------------------------------
    # Event dispatch
    # ------------------------------------------------------------------

    def apply_movement_event(
        self, timestamp: int, source_id: int, spell_id: int, target_id: int
    ) -> None:
        """Applies a spell's movement behavior using dynamic bitflags."""
        spell_data = self.spell_data_dct.get(spell_id)
        if spell_data is None:
            return

        flags = spell_data.flags
        power = spell_data.power
        use_movespeed = bool(flags & MovementBehavior.USE_MOVESPEED)

        # --- Source-centric effects -----------------------------------
        if source_id in self.game_obj_data_dct:
            if flags & MovementBehavior.MOVE_TOWARDS_TARGET and target_id in self.game_obj_data_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                src_x, src_y = self.get_position(source_id, timestamp)
                # Keyed by source_id: an object chasing something is pushing
                # itself, so it composes with (rather than clobbers) its WASD.
                self.apply_velocity(
                    target_id=source_id,
                    source_id=source_id,
                    dir_x=tar_x - src_x,
                    dir_y=tar_y - src_y,
                    power=power,
                    current_time=timestamp,
                    use_movespeed=use_movespeed,
                )
                return

            if flags & MovementBehavior.STOP_MOVE_TOWARDS_TARGET:
                self.remove_velocity(source_id, source_id, timestamp)
                return

            if flags & MovementBehavior.TELEPORT_TO_TARGET and target_id in self.game_obj_data_dct:
                tar_x, tar_y = self.get_position(target_id, timestamp)
                self.teleport(source_id, tar_x, tar_y, timestamp)
                return

            if flags & MovementBehavior.DESPAWN_SELF:
                self.clear_velocities(source_id, timestamp)
                return

        # --- Target-centric effects -----------------------------------
        if target_id not in self.game_obj_data_dct:
            return

        if flags & MovementBehavior.REMOVE_VELOCITY:
            self.remove_velocity(target_id, source_id, timestamp)
            return

        if flags & MovementBehavior.APPLY_VELOCITY:
            if source_id in self.game_obj_data_dct:
                src_x, src_y = self.get_position(source_id, timestamp)
                tar_x, tar_y = self.get_position(target_id, timestamp)
                dir_x, dir_y = tar_x - src_x, tar_y - src_y
            else:
                dir_x, dir_y = 0.0, 0.0

            if dir_x == 0.0 and dir_y == 0.0:
                # Degenerate (co-located or no source body). Fall back to the
                # spawn offset as an intent vector, else drop the event.
                dir_x = spell_data.spawned_x_offset
                dir_y = spell_data.spawned_y_offset

            self.apply_velocity(
                target_id=target_id,
                source_id=source_id,
                dir_x=dir_x,
                dir_y=dir_y,
                power=power,
                current_time=timestamp,
                use_movespeed=use_movespeed,
            )
            return

        if flags & _WASD_MASK:
            self._apply_wasd(
                target_id, source_id, flags, power, timestamp, use_movespeed
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_objects_in_range(
        self, origin_obj_id: int, range_limit: float, current_time: int
    ) -> List[int]:
        """Returns a list of obj_ids that are within range_limit of the origin_obj_id."""
        if origin_obj_id not in self.game_obj_data_dct:
            return []

        origin_x, origin_y = self.get_position(origin_obj_id, current_time)
        range_sq = range_limit * range_limit
        objects_in_range = []

        for obj_id in self.game_obj_data_dct:
            if obj_id == origin_obj_id:
                continue
            x, y = self.get_position(obj_id, current_time)
            if (x - origin_x) ** 2 + (y - origin_y) ** 2 <= range_sq:
                objects_in_range.append(obj_id)

        return objects_in_range

    def is_within_range(
        self, current_time: int, source_id: int, spell_id: int, target_id: int
    ) -> bool:
        """Returns whether two objects are within range of each other."""
        spell_data = self.spell_data_dct[spell_id]
        range_limit = spell_data.range_limit
        if range_limit <= 0.0:
            return True
        if source_id not in self.game_obj_data_dct or target_id not in self.game_obj_data_dct:
            return False
        source_x, source_y = self.get_position(source_id, current_time)
        target_x, target_y = self.get_position(target_id, current_time)
        dx = source_x - target_x
        dy = source_y - target_y
        return dx * dx + dy * dy <= range_limit * range_limit

    def check_collision(
        self, obj_id_1: int, obj_id_2: int, current_time: int, range_limit: float
    ) -> bool:
        """Checks if two objects' hitboxes are overlapping."""
        if obj_id_1 not in self.game_obj_data_dct or obj_id_2 not in self.game_obj_data_dct:
            return False
        x1, y1 = self.get_position(obj_id_1, current_time)
        x2, y2 = self.get_position(obj_id_2, current_time)
        return (x2 - x1) ** 2 + (y2 - y1) ** 2 <= range_limit ** 2
'''