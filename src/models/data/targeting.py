from typing import Iterable, ValuesView
from enum import Enum, auto
from src.settings import Consts
from .default_ids import DefaultIDs
from src.models.components import GameObj


class Targeting(Enum):
    """ Defines targeting behavior for spell """
    NONE = 0
    SELF = auto()
    TARGET = auto()
    PARENT = auto()
    DEFAULT_FRIENDLY = auto()
    DEFAULT_ENEMY = auto()
    TAB_TO_NEXT = auto()

    def select_target(self, source: GameObj, default_ids: DefaultIDs) -> int:
        assert self not in {Targeting.NONE}, f"obj {source.obj_id} is casting a spell with targeting=NONE"
        if self in {Targeting.SELF}:
            return source.obj_id
        if self in {Targeting.TARGET} and Consts.is_valid_id(source.current_target):
            return source.current_target
        if self in {Targeting.PARENT} and Consts.is_valid_id(source.parent_id):
            return source.parent_id
        if self in {Targeting.DEFAULT_ENEMY}:
            if source.res.team.is_allied:
                return default_ids.boss1_id
            return default_ids.player_id
        if self in {Targeting.DEFAULT_FRIENDLY}:
            return source.obj_id
        if self in {Targeting.TAB_TO_NEXT}:
            if not source.res.team.is_allied:
                return default_ids.player_id
            elif source.current_target == default_ids.boss1_id and default_ids.boss2_exists:
                return default_ids.boss2_id
            elif Consts.is_valid_id(default_ids.boss1_id):
                return default_ids.boss1_id
            else:
                # Not implemented. For now, let's assume boss1 always exist.
                return default_ids.player_id
        return default_ids.missing_target_id

    @staticmethod
    def select_targets_for_aoe(source: GameObj, target: GameObj, all_game_objs: ValuesView[GameObj]) -> Iterable[int]:
        for obj in all_game_objs:
            team_is_hit_by_aoe = obj.res.team.is_valid_aoe_target(source.res.team, target.res.team)
            if team_is_hit_by_aoe and obj.state.is_valid_target and obj.obj_id != target.obj_id:
                yield obj.obj_id
