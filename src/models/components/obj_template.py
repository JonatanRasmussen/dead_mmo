from typing import Optional
from dataclasses import dataclass, field
import json

from src.models.utils.copy_utils import CopyTools
from .controls import Controls
from .game_obj import GameObj
from .status import Status

@dataclass(slots=True)
class ObjTemplate:
    """Positional data for GameObjs"""
    game_obj: GameObj = field(default_factory=GameObj)
    obj_controls: Optional[tuple[Controls, ...]] = None

    @classmethod
    def deserialize(cls, data: str) -> 'ObjTemplate':
        d = json.loads(data) if isinstance(data, str) else data
        controls = None
        if d["oc"] is not None:
            controls = tuple(Controls.deserialize(c) for c in d["oc"])
        return cls(
            game_obj=GameObj.deserialize(d["go"]),
            obj_controls=controls
        )
    def serialize(self) -> str:
        return json.dumps({
            "go": json.loads(self.game_obj.serialize()),
            "oc": (
                [json.loads(c.serialize()) for c in self.obj_controls]
                if self.obj_controls is not None else None
            )
        })

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