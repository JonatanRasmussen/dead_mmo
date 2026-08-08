from dataclasses import dataclass
from typing import Dict, Iterable

from src.settings import Consts
from src.world_state import DefaultIDs
from ._id_gen import IdGen
from ._spell_meta_system import SpellMetaSystem


@dataclass(slots=True)
class ObjIdentity:
    obj_id: int
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell: int = Consts.EMPTY_ID
    spawn_timestamp: int = 0
    is_environment: bool = False


class ObjRegistry:
    """
    Owns object identity and lifetime: id generation, parent links, spawn timestamps
    and the DefaultIDs bookkeeping that used to live on GameObj/WorldState.
    """

    def __init__(self, spell_meta: SpellMetaSystem) -> None:
        self._meta = spell_meta
        self._id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._objs: Dict[int, ObjIdentity] = {}
        self._default_ids: DefaultIDs = DefaultIDs()

    @property
    def default_ids(self) -> DefaultIDs:
        return self._default_ids

    def create_environment(self) -> int:
        assert not self._default_ids.environment_exists, "Environment already initialized."
        obj_id = self._id_gen.generate_new_id()
        self._objs[obj_id] = ObjIdentity(obj_id=obj_id, is_environment=True)
        self._default_ids.environment_id = obj_id
        return obj_id

    def register_spawn(self, timestamp: int, parent_id: int, spell_id: int) -> int:
        """Allocates the new obj_id and records identity + default-id roles."""
        obj_id = self._id_gen.generate_new_id()
        self._objs[obj_id] = ObjIdentity(
            obj_id=obj_id,
            parent_id=parent_id,
            spawned_from_spell=spell_id,
            spawn_timestamp=timestamp,
        )
        self._update_default_ids(obj_id, spell_id)
        return obj_id

    def _update_default_ids(self, obj_id: int, spell_id: int) -> None:
        if self._meta.spawns_boss(spell_id):
            if not self._default_ids.boss1_exists:
                self._default_ids.boss1_id = obj_id
            else:
                assert not self._default_ids.boss2_exists, "Second boss already exists."
                self._default_ids.boss2_id = obj_id
        if self._meta.spawns_player(spell_id):
            assert not self._default_ids.player_exists, "Player already exists."
            self._default_ids.player_id = obj_id

    # ---- queries -------------------------------------------------
    def exists(self, obj_id: int) -> bool:
        return obj_id in self._objs

    def get_parent_id(self, obj_id: int) -> int:
        obj = self._objs.get(obj_id)
        return obj.parent_id if obj else Consts.EMPTY_ID

    def get_spawn_timestamp(self, obj_id: int) -> int:
        obj = self._objs.get(obj_id)
        return obj.spawn_timestamp if obj else 0

    def is_environment(self, obj_id: int) -> bool:
        obj = self._objs.get(obj_id)
        return bool(obj and obj.is_environment)

    def get_all_obj_ids(self) -> Iterable[int]:
        return self._objs.keys()