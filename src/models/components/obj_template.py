from typing import Optional
from dataclasses import dataclass, field

from src.models.utils.copy_utils import CopyTools
from .controls import Controls
from .game_obj import GameObj
from .status import Status

@dataclass(slots=True)
class ObjTemplate:
    """Positional data for GameObjs"""
    game_obj: GameObj = field(default_factory=GameObj)
    obj_controls: Optional[tuple[Controls, ...]] = None

    def create_child(self, obj_id: int, parent: GameObj, spawn_timestamp: int, current_target: int) -> GameObj:
        child = self.create_obj_from_template()
        child.obj_id = obj_id
        child.parent_id=parent.obj_id
        child.loadout.spawn_timestamp=spawn_timestamp
        child.current_target=current_target
        child.state=Status.ALIVE
        child.pos.x += parent.pos.x
        child.pos.y += parent.pos.y
        child.res.team = child.res.team.decide_team_based_on_parent(parent.res.team)
        return child

    def create_obj_from_template(self) -> GameObj:
        return CopyTools.full_copy(self.game_obj)