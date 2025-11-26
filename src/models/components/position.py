import math
from dataclasses import dataclass
import json

from src.settings import Consts
from .distance import Distance

@dataclass(slots=True)
class Position:
    """Positional data for GameObjs"""
    x: Distance = Distance(0.0)
    y: Distance = Distance(0.0)
    angle: float = 0.0
    movement_speed: float = 1.0
    base_size: float = 1.0

    @classmethod
    def deserialize(cls, data: str) -> 'Position':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            x=Distance(d["x"]),
            y=Distance(d["y"]),
            angle=d["a"],
            movement_speed=d["ms"],
            base_size=d["bs"]
        )
    def serialize(self) -> str:
        return json.dumps(
            {
                "x": self.x,
                "y": self.y,
                "a": self.angle,
                "ms": self.movement_speed,
                "bs": self.base_size
            }
        )

    @classmethod
    def create_at(cls, x: float, y: float) -> 'Position':
        return Position(x=Distance(x), y=Distance(y))

    def has_target_within_range(self, target: 'Position', range_limit: float) -> bool:
        dx = self.x - target.x
        dy = self.y - target.y
        return dx * dx + dy * dy <= range_limit * range_limit

    def teleport_to_position(self, new_pos: 'Position') -> None:
        self.x = new_pos.x
        self.y = new_pos.y

    def move_in_direction(self, direction: 'Position', move_speed: float) -> None:
        GLOBAL_MODIFIER = Consts.MOVEMENT_DISTANCE_PER_SECOND / Consts.MOVEMENT_UPDATES_PER_SECOND
        new_x = self.x + direction.x * move_speed * GLOBAL_MODIFIER
        new_y = self.y + direction.y * move_speed * GLOBAL_MODIFIER
        self.teleport_to_position(Position(new_x, new_y))

    def move_up(self, move_speed: float) -> None:
        up = Position.create_at(0.0, 1.0)
        self.move_in_direction(up, move_speed)

    def move_left(self, move_speed: float) -> None:
        left = Position.create_at(-1.0, 0.0)
        self.move_in_direction(left, move_speed)

    def move_down(self, move_speed: float) -> None:
        down = Position.create_at(0.0, -1.0)
        self.move_in_direction(down, move_speed)

    def move_right(self, move_speed: float) -> None:
        right = Position.create_at(1.0, 0.0)
        self.move_in_direction(right, move_speed)

    def move_towards_destination(self, destination: 'Position', move_speed: float) -> None:
        dx = destination.x - self.x
        dy = destination.y - self.y
        distance = math.hypot(dx, dy)
        if not distance == 0.0:
            direction = Position(dx / distance, dy / distance)
            self.move_in_direction(direction, move_speed)