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
        child.initialize_as_child(obj_id, parent, spawn_timestamp, current_target)
        return child

    def create_obj_from_template(self) -> GameObj:
        return CopyTools.full_copy(self.game_obj)