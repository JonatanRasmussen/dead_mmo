from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, ValuesView
from src.settings import Consts


@dataclass(slots=True)
class ObjTargetingData:
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    event_target_id: int = Consts.EMPTY_ID
    player_number: int = 0
    threat_score: int = 0
    is_enemy: bool = False
    is_untargetable: bool = False

class TargetingEffect(str, Enum):
    TARGETSWAP_TO_EVENT_TARGET = "targetswap_to_event_target"
    TARGETSWAP_TO_PARENT = "targetswap_to_parent"
    TARGETSWAP_TO_PARENTS_TARGET = "targetswap_to_parents_target"
    SWAP_TEAM = "teamswap"
    IS_UNTARGETABLE = "is_untargetable"
    APPLY_THREAT_SCORE = "threat_score"
    APPLY_PLAYER_NUMBER = "player_number"

class TargetingInvalidOutcomes(str, Enum):
    SOURCE_IS_UNTARGETABLE = "source_is_untargetable"
    TARGET_IS_UNTARGETABLE = "target_is_untargetable"
    TARGET_IS_NOT_SAME_TEAM = "target_is_not_same_team"
    TARGET_IS_NOT_OTHER_TEAM = "target_is_not_other_team"

class TargetingValidation(str, Enum):
    IS_SOURCE_TARGETABLE = "is_source_targetable"
    IS_TARGET_TARGETABLE = "is_target_targetable"
    IS_TARGET_SAME_TEAM = "is_target_same_team"
    IS_TARGET_OTHER_TEAM = "is_target_other_team"

class TargetingSystem:
    def __init__(self) -> None:
        self._data_dct: dict[int, ObjTargetingData] = {}

        self.targetable_ids_on_player_team: set[int] = set()
        self.targetable_ids_on_enemy_team: set[int] = set()
        self.player_id: int = Consts.EMPTY_ID
        self.boss_id: int = Consts.EMPTY_ID

    def spawn_game_obj(self, new_obj_id: int, parent_id: int, target_id: int) -> None:
        is_enemy = self.get_data(parent_id).is_enemy if parent_id in self._data_dct else False
        game_obj = ObjTargetingData(obj_id=new_obj_id, parent_id=parent_id, event_target_id=target_id, is_enemy=is_enemy)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjTargetingData(obj_id=obj_id, event_target_id=obj_id, is_untargetable=True)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjTargetingData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

        if not new_obj.is_untargetable:
            if new_obj.is_enemy:
                self.targetable_ids_on_enemy_team.add(new_obj_id)
            else:
                self.targetable_ids_on_player_team.add(new_obj_id)

    def get_data(self, obj_id: int) -> ObjTargetingData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self._data_dct.pop(obj_id, None)
        self.targetable_ids_on_player_team.discard(obj_id)
        self.targetable_ids_on_enemy_team.discard(obj_id)

    # ---- Lookups ----
    def view_all_data(self) -> ValuesView[ObjTargetingData]:
        return self._data_dct.values()

    def get_parent_data(self, obj_id: int) -> ObjTargetingData:
        obj_data = self.get_data(obj_id)
        parent_id = obj_data.parent_id
        if parent_id == Consts.EMPTY_ID or parent_id == obj_id:
            print(f"Warning: Obj {obj_id}'s parent {parent_id} has unexpected configuration.")
            return obj_data
        return self.get_data(parent_id)

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self._data_dct.get(obj_id, ObjTargetingData()).event_target_id

    def select_targets_for_aoe(self, source_id: int, hits_cross_team: bool, hits_same_team: bool) -> Iterable[int]:
        if not hits_cross_team and not hits_same_team: return
        source_data = self._data_dct.get(source_id)
        if not source_data: return

        if hits_same_team:
            target_set = self.targetable_ids_on_enemy_team if source_data.is_enemy else self.targetable_ids_on_player_team
            for obj_id in target_set:
                yield obj_id

        if hits_cross_team:
            target_set = self.targetable_ids_on_player_team if source_data.is_enemy else self.targetable_ids_on_enemy_team
            for obj_id in target_set:
                yield obj_id

    def validate_event(self, validation_type: str, source_id: int, target_id: int) -> str:
        if validation_type == TargetingValidation.IS_SOURCE_TARGETABLE:
            if self.get_data(source_id).is_untargetable:
                return TargetingInvalidOutcomes.SOURCE_IS_UNTARGETABLE.value
        if validation_type == TargetingValidation.IS_TARGET_TARGETABLE:
            if self.get_data(target_id).is_untargetable:
                return TargetingInvalidOutcomes.TARGET_IS_UNTARGETABLE.value
        if validation_type == TargetingValidation.IS_TARGET_SAME_TEAM:
            if self.get_data(source_id).is_enemy != self.get_data(target_id).is_enemy:
                return TargetingInvalidOutcomes.TARGET_IS_NOT_SAME_TEAM.value
        if validation_type == TargetingValidation.IS_TARGET_OTHER_TEAM:
            if self.get_data(source_id).is_enemy == self.get_data(target_id).is_enemy:
                return TargetingInvalidOutcomes.TARGET_IS_NOT_OTHER_TEAM.value
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, source_id: int, target_id: int) -> None:
        if effect_type == TargetingEffect.TARGETSWAP_TO_EVENT_TARGET:
            self.get_data(source_id).event_target_id = target_id
        elif effect_type == TargetingEffect.TARGETSWAP_TO_PARENT:
            data = self.get_data(source_id)
            data.event_target_id = data.parent_id
        elif effect_type == TargetingEffect.TARGETSWAP_TO_PARENTS_TARGET:
            data = self.get_data(source_id)
            parent_data = self.get_parent_data(source_id)
            data.event_target_id = parent_data.event_target_id
        elif effect_type == TargetingEffect.APPLY_THREAT_SCORE:
            self.get_data(source_id).threat_score += int(effect_value)
        elif effect_type == TargetingEffect.APPLY_PLAYER_NUMBER:
            self.get_data(source_id).player_number += int(effect_value)
            self.player_id = source_id
        elif effect_type == TargetingEffect.SWAP_TEAM:
            data = self.get_data(source_id)
            data.is_enemy = not data.is_enemy
            if not data.is_untargetable:
                if data.is_enemy:
                    self.targetable_ids_on_player_team.remove(source_id)
                    self.targetable_ids_on_enemy_team.add(source_id)
                else:
                    self.targetable_ids_on_enemy_team.remove(source_id)
                    self.targetable_ids_on_player_team.add(source_id)
        elif effect_type == TargetingEffect.IS_UNTARGETABLE:
            data = self.get_data(source_id)
            was_untargetable = data.is_untargetable
            data.is_untargetable = bool(effect_value)
            if was_untargetable != data.is_untargetable:
                target_set = self.targetable_ids_on_enemy_team if data.is_enemy else self.targetable_ids_on_player_team
                if data.is_untargetable:
                    target_set.remove(source_id)
                else:
                    target_set.add(source_id)
