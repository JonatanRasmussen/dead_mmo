from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, ValuesView
from src.settings import Consts

@dataclass(slots=True)
class ObjCastingData:
    spawn_timestamp: int = 0
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell_id: int = Consts.EMPTY_ID
    current_target_id: int = Consts.EMPTY_ID
    gcd_start: int = -10000
    gcd_end: int = 0
    cooldown_start: int = -10000
    cooldown_end: int = 0
    castbar_spell_id: int = Consts.EMPTY_ID
    castbar_start: int = -10000
    castbar_duration: int = 0
    castbar_ticks: int = 0
    player_number: int = 0
    threat_score: int = 0
    is_enemy: bool = False
    is_untargetable: bool = False

    @classmethod
    def create_new_obj(cls, timestamp: int, parent_id: int, new_obj_id: int, spell_id: int, target_id: int, is_enemy: bool) -> "ObjCastingData":
        return cls(
            spawn_timestamp=timestamp,
            obj_id=new_obj_id,
            parent_id=parent_id,
            spawned_from_spell_id=spell_id,
            current_target_id=target_id,
            is_enemy=is_enemy,
        )

class CastingEffect(str, Enum):
    APPLY_TICKS_ADDITION = "add_channeling_ticks"
    APPLY_TICKS_SUBTRACTION = "consume_channeling_ticks"
    APPLY_GCD = "gcd_duration"
    APPLY_COOLDOWN = "base_cooldown"
    APPLY_PARENT_CD = "apply_parent_cd"
    SELECT_SPELL_ID = "select_spell_id"
    TARGETSWAP_TO_TARGET = "targetswap_to_target"
    TARGETSWAP_TO_PARENT = "targetswap_to_parent"
    TARGETSWAP_TO_PARENTS_TARGET = "targetswap_to_parents_target"
    SWAP_TEAM = "teamswap"
    IS_UNTARGETABLE = "is_untargetable"
    APPLY_THREAT_SCORE = "threat_score"
    APPLY_PLAYER_NUMBER = "player_number"

class CastingInvalidOutcomes(str, Enum):
    TICKS_NOT_READY = "out_of_channeling_ticks"
    GCD_NOT_READY = "gcd_not_ready"
    COOLDOWN_NOT_READY = "cooldown_not_ready"
    PARENT_COOLDOWN_NOT_READY = "parent_cooldown_not_ready"
    INVALID_SPELL_SELECTED = "invalid_spell_selected"
    SOURCE_IS_UNTARGETABLE = "source_is_untargetable"
    TARGET_IS_UNTARGETABLE = "target_is_untargetable"
    TARGET_IS_NOT_SAME_TEAM = "target_is_not_same_team"
    TARGET_IS_NOT_OTHER_TEAM = "target_is_not_other_team"

class CastingValidation(str, Enum):
    ARE_TICKS_READY = "has_channeling_ticks"
    IS_GCD_READY = "is_gcd_ready"
    IS_COOLDOWN_READY = "is_cooldown_ready"
    IS_PARENT_CD_READY = "is_parent_cooldown_ready"
    IS_SPELL_SELECTED = "is_spell_selected"
    IS_SOURCE_TARGETABLE = "is_source_targetable"
    IS_TARGET_TARGETABLE = "is_target_targetable"
    IS_TARGET_SAME_TEAM = "is_target_same_team"
    IS_TARGET_OTHER_TEAM = "is_target_other_team"

class CastingSystem:

    def __init__(self) -> None:
        self._data_dct: dict[int, ObjCastingData] = {}
        self.targetable_ids_on_player_team: set[int] = set()
        self.targetable_ids_on_enemy_team: set[int] = set()
        self.player_id: int = Consts.EMPTY_ID
        self.boss_id: int = Consts.EMPTY_ID

    def spawn_game_obj(self, timestamp: int, parent_id: int, new_obj_id: int, spell_id: int, target_id: int = Consts.EMPTY_ID) -> None:
        parent_data = self.get_data(parent_id)
        is_enemy = parent_data.is_enemy
        game_obj = ObjCastingData.create_new_obj(timestamp, parent_id, new_obj_id, spell_id, target_id, is_enemy)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjCastingData(obj_id=obj_id, current_target_id=obj_id, is_untargetable=True)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjCastingData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj
        if not new_obj.is_untargetable:
            if new_obj.is_enemy:
                self.targetable_ids_on_enemy_team.add(new_obj_id)
            else:
                self.targetable_ids_on_player_team.add(new_obj_id)

    def get_data(self, obj_id: int) -> ObjCastingData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)
        self.targetable_ids_on_player_team.discard(obj_id)
        self.targetable_ids_on_enemy_team.discard(obj_id)

    # ---- Lookups ----

    def view_all_data(self) -> ValuesView[ObjCastingData]:
        #OBJ_IDS WERE INSERTED INTO THE DICT ONE AT A TIME IN ASCENDING ORDER!
        return self._data_dct.values()

    def get_parent_data(self, obj_id: int) -> ObjCastingData:
        obj_data = self.get_data(obj_id)
        parent_id = obj_data.parent_id
        if parent_id == Consts.EMPTY_ID or parent_id == obj_id:
            print(f"Warning: Obj {obj_id}'s parent {parent_id} has unexpected configuration.")
            return obj_data
        return self.get_data(parent_id)

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self._data_dct.get(obj_id, ObjCastingData()).current_target_id

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

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> str:
        if validation_type == CastingValidation.ARE_TICKS_READY:
            if self.get_data(source_id).castbar_ticks < round(validation_value):
                return CastingInvalidOutcomes.TICKS_NOT_READY.value
        if validation_type == CastingValidation.IS_GCD_READY:
            if self.get_data(source_id).gcd_end > timestamp:
                return CastingInvalidOutcomes.GCD_NOT_READY.value
        if validation_type == CastingValidation.IS_COOLDOWN_READY:
            if self.get_data(source_id).cooldown_end > timestamp:
                return CastingInvalidOutcomes.COOLDOWN_NOT_READY.value
        if validation_type == CastingValidation.IS_PARENT_CD_READY:
            parent_data = self.get_parent_data(source_id)
            if parent_data.cooldown_end > timestamp:
                return CastingInvalidOutcomes.PARENT_COOLDOWN_NOT_READY.value
        if validation_type == CastingValidation.IS_SPELL_SELECTED:
            if self.get_data(source_id).castbar_spell_id != round(validation_value):
                return CastingInvalidOutcomes.INVALID_SPELL_SELECTED.value
        if validation_type == CastingValidation.IS_SOURCE_TARGETABLE:
            if self.get_data(source_id).is_untargetable:
                return CastingInvalidOutcomes.SOURCE_IS_UNTARGETABLE.value
        if validation_type == CastingValidation.IS_TARGET_TARGETABLE:
            if self.get_data(target_id).is_untargetable:
                return CastingInvalidOutcomes.TARGET_IS_UNTARGETABLE.value
        if validation_type == CastingValidation.IS_TARGET_SAME_TEAM:
            if self.get_data(source_id).is_enemy != self.get_data(target_id).is_enemy:
                return CastingInvalidOutcomes.TARGET_IS_NOT_SAME_TEAM.value
        if validation_type == CastingValidation.IS_TARGET_OTHER_TEAM:
            if self.get_data(source_id).is_enemy == self.get_data(target_id).is_enemy:
                return CastingInvalidOutcomes.TARGET_IS_NOT_OTHER_TEAM.value
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if effect_type == CastingEffect.APPLY_TICKS_ADDITION:
            self.get_data(source_id).castbar_ticks += round(effect_value)
        elif effect_type == CastingEffect.APPLY_TICKS_SUBTRACTION:
            self.get_data(source_id).castbar_ticks -= max(0, round(effect_value))
        elif effect_type == CastingEffect.APPLY_GCD:
            other_data = self.get_data(source_id)
            other_data.gcd_start = timestamp
            other_data.gcd_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.APPLY_COOLDOWN:
            other_data = self.get_data(source_id)
            other_data.cooldown_start = timestamp
            other_data.cooldown_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.APPLY_PARENT_CD:
            parent_data = self.get_parent_data(source_id)
            parent_data.cooldown_start = timestamp
            parent_data.cooldown_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.SELECT_SPELL_ID:
            self.get_data(source_id).castbar_spell_id = round(effect_value)
        elif effect_type == CastingEffect.TARGETSWAP_TO_TARGET:
            self.get_data(source_id).current_target_id = target_id
        elif effect_type == CastingEffect.TARGETSWAP_TO_PARENT:
            data = self.get_data(source_id)
            data.current_target_id = data.parent_id
        elif effect_type == CastingEffect.TARGETSWAP_TO_PARENTS_TARGET:
            data = self.get_data(source_id)
            parent_data = self.get_parent_data(source_id)
            data.current_target_id = parent_data.current_target_id
        elif effect_type == CastingEffect.APPLY_THREAT_SCORE:
            self.get_data(source_id).threat_score += int(effect_value)
        elif effect_type == CastingEffect.APPLY_PLAYER_NUMBER:
            self.get_data(source_id).player_number += int(effect_value)
            self.player_id = source_id
        elif effect_type == CastingEffect.SWAP_TEAM:
            data = self.get_data(source_id)
            data.is_enemy = not data.is_enemy
            if not data.is_untargetable:
                if data.is_enemy:
                    self.targetable_ids_on_player_team.remove(source_id)
                    self.targetable_ids_on_enemy_team.add(source_id)
                else:
                    self.targetable_ids_on_enemy_team.remove(source_id)
                    self.targetable_ids_on_player_team.add(source_id)
        elif effect_type == CastingEffect.IS_UNTARGETABLE:
            data = self.get_data(source_id)
            was_untargetable = data.is_untargetable
            data.is_untargetable = bool(effect_value)
            if was_untargetable != data.is_untargetable:
                target_set = self.targetable_ids_on_enemy_team if data.is_enemy else self.targetable_ids_on_player_team
                if data.is_untargetable:
                    target_set.remove(source_id)
                else:
                    target_set.add(source_id)