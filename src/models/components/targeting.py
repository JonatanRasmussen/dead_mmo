from typing import List, Tuple, Iterable, Optional, NamedTuple, ValuesView
from enum import Enum, auto
from src.config import Consts
from .important_ids import ImportantIDs
from .game_obj import GameObj


class Targeting(Enum):
    """ Defines targeting behavior for spell """
    NONE = 0
    SELF = auto()
    PARENT = auto()
    AURA_TARGET = auto()
    CURRENT_TARGET = auto()
    DEFAULT_FRIENDLY = auto()
    DEFAULT_ENEMY = auto()
    TAB_TO_NEXT = auto()

    @property
    def is_target_swap(self) -> bool:
        return self in {Targeting.TAB_TO_NEXT}

    def select_target(self, source: GameObj, aura_target: int, important_ids: ImportantIDs) -> int:
        assert self not in {Targeting.NONE}, f"obj {source.obj_id} is casting a spell with targeting=NONE"
        if self in {Targeting.SELF}:
            return source.obj_id
        if self in {Targeting.AURA_TARGET} and Consts.is_valid_id(aura_target):
            return aura_target
        if self in {Targeting.CURRENT_TARGET} and Consts.is_valid_id(aura_target):
            return source.current_target
        if self in {Targeting.PARENT} and Consts.is_valid_id(source.parent_id):
            return source.parent_id
        if self in {Targeting.DEFAULT_ENEMY}:
            if source.is_allied:
                return important_ids.boss1_id
            return important_ids.player_id
        if self in {Targeting.DEFAULT_FRIENDLY}:
            return source.obj_id
        if self.is_target_swap:
            if self in {Targeting.TAB_TO_NEXT}:
                if not source.is_allied:
                    return important_ids.player_id
                elif source.current_target == important_ids.boss1_id and important_ids.boss2_exists:
                    return important_ids.boss2_id
                elif Consts.is_valid_id(important_ids.boss1_id):
                    return important_ids.boss1_id
                else:
                    # Not implemented. For now, let's assume boss1 always exist.
                    return important_ids.player_id
        return important_ids.missing_target_id

    @staticmethod
    def select_targets_for_aoe(source: GameObj, target: GameObj, all_game_objs: ValuesView[GameObj]) -> Iterable[int]:
        for obj in all_game_objs:
            obj_meets_team_criteria = source.is_same_team(target) == obj.is_same_team(source)
            if obj_meets_team_criteria and obj.status.is_valid_target and obj.obj_id != target.obj_id:
                yield obj.obj_id
