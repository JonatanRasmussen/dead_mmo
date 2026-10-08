from dataclasses import dataclass
from src.settings import Consts


@dataclass(slots=True)
class GameObj:
    obj_id: int = Consts.EMPTY_OBJ_ID
    spawn_timestamp: int = Consts.EMPTY_TIMESTAMP
    _parent_id: int = Consts.EMPTY_OBJ_ID
    origin_id: int = Consts.EMPTY_SPELL_ID
    destination_id: int = Consts.EMPTY_OBJ_ID

    @property
    def parent_id(self) -> int:
        if self._parent_id == Consts.EMPTY_OBJ_ID:
            return self.obj_id
        return self._parent_id

    @classmethod
    def create_new(cls, obj_id: int, spawn_timestamp: int, parent_id: int, origin_id: int, destination_id: int) -> 'GameObj':
        return GameObj(obj_id=obj_id, spawn_timestamp=spawn_timestamp, _parent_id=parent_id, origin_id=origin_id, destination_id=destination_id)