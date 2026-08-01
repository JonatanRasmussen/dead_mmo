
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import IntFlag, auto


from ._spell_database import SpellDatabase
from src.world_state.spell_system import Spell, Behavior
from src.models.components import Position
# Assuming Behavior is importable from your project structure (e.g., src.world_state.behavior)


class MovementBehavior(IntFlag):
    """ Various bitflags that define spell behavior. """
    NONE = 0

    # MOVEMENT
    STEP_UP = auto()
    STEP_LEFT = auto()
    STEP_DOWN = auto()
    STEP_RIGHT = auto()
    MOVE_TOWARDS_TARGET = auto()
    TELEPORT_TO_TARGET = auto()
    FORCE_MOVE = auto()
    TRY_MOVE = auto()

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
    timestamp: int
    movespeed: float = 1.0


class MovementSystem:
    """
    Manages all movement-related logic, geometry, and hitboxes using a dead reckoning design.
    Positional data is calculated via time-deltas rather than per-frame updates.

    OLD INSTRUCTIONS FOR CLASS CREATION (DELETE LATER)
    # Everything that happens in my (for now, 2D) game is driven by events that have a spell_id and a target_id (game_obj)
    # At the start of the game, the behavior of each spell is loaded into memory via load_spell (managed by an external script).
    # For now, this spell behavior data is provided via a Spell class which I will delete in the future. The Spell class should not be used elsewhere in this class.
    # Throughout the game, spell_ids are provided via events as well as a target game_obj. This class should look up and apply the spell to the game_obj.
    # Spells can be something as simple as "Move_Left". Everything is a spell. All movement will happen via some spell_id.
    # Beyond containing spell behavior data for each spell_id, it also contains all movement-related data for each game_obj, indexed by obj_id (entity component system -inspired design)
    # The game_obj movement data should use a dead reckoning design. x_pos, y_pos, x_vel, y_vel (floats) as well as a timestamp (int) at which the movement started
    # A game_objs positional data is then accessed via an obj_id and a timestamp. 1 timestamp unit = 1 ms. Calculate an objs position based on time-delta. We are not updating positional data each frame, only when changing movement velocity or pos.
    # This class should also handle geometry and distance-based logic and hitboxes, for example "return obj_ids that are within some_variable range of some_obj_id.
    """

    def __init__(self, spell_database: SpellDatabase) -> None:
        # Maps spell_id -> SpellMovementData
        self.spell_data_dct: Dict[int, SpellMovementData] = MovementSystem._create_initialized_spell_data_dct(spell_database)
        # Maps obj_id -> MovementData
        self.game_obj_positions_dct: Dict[int, ObjMovementData] = {}

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
            spawned_x_offset=spell.get_spawned_obj_pos_xy_speed[0],
            spawned_y_offset=spell.get_spawned_obj_pos_xy_speed[1],
            spawned_movespeed=spell.get_spawned_obj_movespeed,
        )
        return spell_data_dct

    def apply_movement(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        """
        Applies a spell's movement behavior to a target object.
        `reference_id` is used for relational movement (e.g., MOVE_TOWARDS_TARGET).
        """
        if spell_id not in self.spell_data_dct or source_id not in self.game_obj_positions_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_positions_dct[source_id]
        # Convert movement speed from units/sec to units/ms. Modified by spell power.
        speed_per_ms = (source_data.movespeed * spell_data.power) / 1000.0
        # Apply movement based on Behavior bitflags
        if flags & MovementBehavior.STEP_UP.value:
            self.set_velocity(source_id, 0.0, speed_per_ms, timestamp)
        elif flags & MovementBehavior.STEP_DOWN.value:
            self.set_velocity(source_id, 0.0, -speed_per_ms, timestamp)
        elif flags & MovementBehavior.STEP_LEFT.value:
            self.set_velocity(source_id, -speed_per_ms, 0.0, timestamp)
        elif flags & MovementBehavior.STEP_RIGHT.value:
            self.set_velocity(source_id, speed_per_ms, 0.0, timestamp)
        elif flags & MovementBehavior.MOVE_TOWARDS_TARGET.value and target_id is not None:
            if target_id in self.game_obj_positions_dct:
                ref_x, ref_y = self.get_position(target_id, timestamp)
                tar_x, tar_y = self.get_position(source_id, timestamp)
                dx = ref_x - tar_x
                dy = ref_y - tar_y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    vx = (dx / dist) * speed_per_ms
                    vy = (dy / dist) * speed_per_ms
                    self.set_velocity(source_id, vx, vy, timestamp)
        elif flags & MovementBehavior.TELEPORT_TO_TARGET.value and target_id is not None:
            if target_id in self.game_obj_positions_dct:
                ref_x, ref_y = self.get_position(target_id, timestamp)
                self.teleport(source_id, ref_x, ref_y, timestamp)
        elif flags == MovementBehavior.NONE.value:
            # If a spell has no movement flags (e.g., a "Stop_Moving" spell), halt velocity
            self.set_velocity(source_id, 0.0, 0.0, timestamp)

    def spawn_game_obj(self, timestamp: int, parent_obj_id: int, spawned_obj_id: int, spell_id: int) -> None:
        """Registers a GameObj into the movement system, extracting its initial state."""
        spell_data = self.spell_data_dct[spell_id]
        parent_pos = self.game_obj_positions_dct[parent_obj_id]
        self.game_obj_positions_dct[spawned_obj_id] = ObjMovementData(
            x_pos=float(parent_pos.x_pos + spell_data.spawned_x_offset),
            y_pos=float(parent_pos.y_pos + spell_data.spawned_y_offset),
            x_vel=0.0,
            y_vel=0.0,
            timestamp=timestamp,
            movespeed=spell_data.spawned_movespeed,
        )

    def despawn_game_obj(self, obj_id: int) -> None:
        """Removes an object from the movement system (e.g., on despawn)."""
        self.game_obj_positions_dct.pop(obj_id, None)

    def get_position(self, obj_id: int, current_time: int) -> Tuple[float, float]:
        """Calculates the current (x, y) position of an object using dead reckoning."""
        if obj_id not in self.game_obj_positions_dct:
            raise ValueError(f"Object {obj_id} not found in MovementSystem.")

        data = self.game_obj_positions_dct[obj_id]

        # 1 timestamp unit = 1 ms
        dt = current_time - data.timestamp

        # Velocity is stored in units per millisecond
        current_x = data.x_pos + (data.x_vel * dt)
        current_y = data.y_pos + (data.y_vel * dt)

        return current_x, current_y

    def _update_base_position(self, obj_id: int, current_time: int) -> None:
        """Bakes the current velocity into the base position and updates the timestamp."""
        x, y = self.get_position(obj_id, current_time)
        data = self.game_obj_positions_dct[obj_id]
        data.x_pos = x
        data.y_pos = y
        data.timestamp = current_time

    def set_velocity(self, obj_id: int, vx: float, vy: float, current_time: int) -> None:
        """Updates the velocity of an object, resetting its base position to the current time."""
        if obj_id not in self.game_obj_positions_dct:
            return

        self._update_base_position(obj_id, current_time)
        data = self.game_obj_positions_dct[obj_id]
        data.x_vel = vx
        data.y_vel = vy

    def teleport(self, obj_id: int, x: float, y: float, current_time: int) -> None:
        """Instantly moves an object to a new position, halting its velocity."""
        if obj_id not in self.game_obj_positions_dct:
            return

        data = self.game_obj_positions_dct[obj_id]
        data.x_pos = x
        data.y_pos = y
        data.x_vel = 0.0
        data.y_vel = 0.0
        data.timestamp = current_time

    def apply_spell_event(self, spell_id: int, target_id: int, current_time: int, reference_id: Optional[int] = None) -> None:
        """
        Applies a spell's movement behavior to a target object.
        `reference_id` is used for relational movement (e.g., MOVE_TOWARDS_TARGET).
        """
        if spell_id not in self.spell_data_dct or target_id not in self.game_obj_positions_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        target_data = self.game_obj_positions_dct[target_id]

        # Convert movement speed from units/sec to units/ms. Modified by spell power.
        speed_per_ms = (target_data.movespeed * spell_data.power) / 1000.0

        # Apply movement based on Behavior bitflags
        if flags & MovementBehavior.STEP_UP.value:
            self.set_velocity(target_id, 0.0, speed_per_ms, current_time)

        elif flags & MovementBehavior.STEP_DOWN.value:
            self.set_velocity(target_id, 0.0, -speed_per_ms, current_time)

        elif flags & MovementBehavior.STEP_LEFT.value:
            self.set_velocity(target_id, -speed_per_ms, 0.0, current_time)

        elif flags & MovementBehavior.STEP_RIGHT.value:
            self.set_velocity(target_id, speed_per_ms, 0.0, current_time)

        elif flags & MovementBehavior.MOVE_TOWARDS_TARGET.value and reference_id is not None:
            if reference_id in self.game_obj_positions_dct:
                ref_x, ref_y = self.get_position(reference_id, current_time)
                tar_x, tar_y = self.get_position(target_id, current_time)

                dx = ref_x - tar_x
                dy = ref_y - tar_y
                dist = math.hypot(dx, dy)

                if dist > 0:
                    vx = (dx / dist) * speed_per_ms
                    vy = (dy / dist) * speed_per_ms
                    self.set_velocity(target_id, vx, vy, current_time)

        elif flags & MovementBehavior.TELEPORT_TO_TARGET.value and reference_id is not None:
            if reference_id in self.game_obj_positions_dct:
                ref_x, ref_y = self.get_position(reference_id, current_time)
                self.teleport(target_id, ref_x, ref_y, current_time)

        elif flags == MovementBehavior.NONE.value:
            # If a spell has no movement flags (e.g., a "Stop_Moving" spell), halt velocity
            self.set_velocity(target_id, 0.0, 0.0, current_time)

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

    def check_collision(self, obj_id_1: int, obj_id_2: int, current_time: int, range_limit: float) -> bool:
        """Checks if two objects' hitboxes are overlapping."""
        if obj_id_1 not in self.game_obj_positions_dct or obj_id_2 not in self.game_obj_positions_dct:
            return False

        x1, y1 = self.get_position(obj_id_1, current_time)
        x2, y2 = self.get_position(obj_id_2, current_time)

        dist_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        collision_distance_sq = range_limit ** 2

        return dist_sq <= collision_distance_sq