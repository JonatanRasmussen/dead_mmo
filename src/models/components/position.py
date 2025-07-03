import math

from dataclasses import dataclass

from src.config import Consts

@dataclass(slots=True)
class Position:
    """Positional data for GameObjs"""
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0

    def has_target_within_range(self, target: 'Position', range_limit: float) -> bool:
        return (self.x - target.x) ** 2 + (self.y - target.y) ** 2 <= range_limit ** 2

    def teleport_to_position(self, new_pos: 'Position') -> None:
        self.x = new_pos.x
        self.y = new_pos.y

    def move_in_direction(self, direction: 'Position', move_speed: float) -> None:
        GLOBAL_MODIFIER = Consts.MOVEMENT_DISTANCE_PER_SECOND / Consts.MOVEMENT_UPDATES_PER_SECOND
        new_x = self.x + direction.x * move_speed * GLOBAL_MODIFIER
        new_y = self.y + direction.y * move_speed * GLOBAL_MODIFIER
        self.teleport_to_position(Position(new_x, new_y))

    def move_towards_destination(self, destination: 'Position', move_speed: float) -> None:
        dx = destination.x - self.x
        dy = destination.y - self.y
        distance = math.hypot(dx, dy)
        if not distance == 0:
            direction = Position(dx / distance, dy / distance)
            self.move_in_direction(direction, move_speed)