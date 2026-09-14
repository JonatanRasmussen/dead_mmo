from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable
from src.settings import Consts

@dataclass(slots=True)
class ObjCastingData:
    spawn_timestamp: int = 0
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell_id: int = Consts.EMPTY_ID
    ability_cd_start: dict[int, int] = field(default_factory=dict)
    gcd_start: int = -10000
    gcd_end: int = 0
    cooldown_start: int = -10000
    cooldown_end: int = 0
    castbar_spell_id: int = Consts.EMPTY_ID
    castbar_start: int = -10000
    castbar_duration: int = 0
    castbar_ticks: int = 0
    current_target_id: int = Consts.EMPTY_ID
    is_enemy: bool = False
    is_boss_or_player: bool = False
    is_combat_participant: bool = True

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
    UPDATE_CURRENT_TARGET = "update_current_target"
    TARGETSWAP_TO_OTHER_TEAM = "targetswap_to_other_team"
    TARGETSWAP_TO_PARENT = "targetswap_to_parent"
    TEAMSWAP = "teamswap"
    BECOME_UNTARGETABLE = "become_untargetable"
    IS_ENEMY = "is_enemy"
    IS_BOSS = "is_boss"
    IS_PLAYER = "is_player"

class CastingInvalidOutcomes(str, Enum):
    INVALID_TICKS_READY = "out_of_channeling_ticks"
    INVALID_GCD_READY = "gcd_not_ready"
    INVALID_COOLDOWN_READY = "cooldown_not_ready"
    SOURCE_IS_DISABLED = "source_is_disabled"
    TARGET_IS_INVALID = "target_is_invalid"

class CastingValidation(str, Enum):
    VALIDATE_TICKS_READY = "has_channeling_ticks"
    VALIDATE_GCD_READY = "is_gcd_ready"
    VALIDATE_COOLDOWN_READY = "is_cooldown_ready"
    SOURCE_IS_VALID = "source_is_valid"

class CastingSystem:

    def __init__(self) -> None:
        self._data_dct: Dict[int, ObjCastingData] = {}
        self.player_id: int = Consts.EMPTY_ID
        self.boss_id: int = Consts.EMPTY_ID

    def spawn_game_obj(self, timestamp: int, parent_id: int, new_obj_id: int, spell_id: int, target_id: int = Consts.EMPTY_ID) -> None:
        parent_data = self._data_dct.get(parent_id)
        final_is_enemy = parent_data.is_enemy if parent_data else False
        game_obj = ObjCastingData.create_new_obj(timestamp, parent_id, new_obj_id, spell_id, target_id, final_is_enemy)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjCastingData(obj_id=obj_id, current_target_id=obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjCastingData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjCastingData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

    # ---- Lookups ----

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self._data_dct.get(obj_id, ObjCastingData()).current_target_id

    def _is_valid_target(self, obj_id: int) -> bool:
        data = self._data_dct.get(obj_id)
        return data is not None and data.is_combat_participant

    def select_targets_for_aoe(self, source_id: int, hits_cross_team: bool, hits_same_team: bool) -> Iterable[int]:
        if not hits_cross_team and not hits_same_team: return
        source_data = self._data_dct.get(source_id)
        if not source_data: return

        for obj_id, obj_data in self._data_dct.items():
            if not obj_data.is_combat_participant: continue
            is_opposite_team = (obj_data.is_enemy != source_data.is_enemy)
            if (is_opposite_team and hits_cross_team) or (not is_opposite_team and hits_same_team):
                yield obj_id

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> str:
        if validation_type == CastingValidation.VALIDATE_TICKS_READY:
            if self.get_data(source_id).castbar_ticks < round(validation_value):
                return CastingInvalidOutcomes.INVALID_TICKS_READY.value
        if validation_type == CastingValidation.VALIDATE_GCD_READY:
            if self.get_data(source_id).gcd_end > timestamp:
                return CastingInvalidOutcomes.INVALID_GCD_READY.value
        if validation_type == CastingValidation.VALIDATE_COOLDOWN_READY:
            if self.get_data(source_id).cooldown_end > timestamp:
                return CastingInvalidOutcomes.INVALID_COOLDOWN_READY.value
        if validation_type == CastingValidation.SOURCE_IS_VALID:
            if not self._is_valid_target(source_id):
                return CastingInvalidOutcomes.SOURCE_IS_DISABLED.value
            if not self._is_valid_target(target_id) and source_id != target_id:
                return CastingInvalidOutcomes.TARGET_IS_INVALID.value
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if effect_type == CastingEffect.APPLY_TICKS_ADDITION:
            self.get_data(source_id).castbar_ticks += round(effect_value)
        elif effect_type == CastingEffect.APPLY_TICKS_SUBTRACTION:
            self.get_data(source_id).castbar_ticks -= max(0, round(effect_value))
        elif effect_type == CastingEffect.APPLY_GCD:
            obj_data = self.get_data(source_id)
            obj_data.gcd_start = timestamp
            obj_data.gcd_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.APPLY_COOLDOWN:
            obj_data = self.get_data(source_id)
            obj_data.cooldown_start = timestamp
            obj_data.cooldown_end = timestamp + round(effect_value)
        elif effect_type == CastingEffect.UPDATE_CURRENT_TARGET:
            self.get_data(source_id).current_target_id = target_id
        elif effect_type == CastingEffect.TARGETSWAP_TO_OTHER_TEAM:
            data = self.get_data(source_id)
            data.current_target_id = self.player_id if data.is_enemy else self.boss_id
        elif effect_type == CastingEffect.TARGETSWAP_TO_PARENT:
            data = self.get_data(source_id)
            data.current_target_id = data.parent_id
        elif effect_type == CastingEffect.TEAMSWAP:
            self.get_data(source_id).is_enemy = not self.get_data(source_id).is_enemy
        elif effect_type == CastingEffect.BECOME_UNTARGETABLE:
            self.get_data(source_id).is_combat_participant = False
        elif effect_type == CastingEffect.IS_ENEMY:
            self.get_data(source_id).is_enemy = bool(effect_value)
        elif effect_type == CastingEffect.IS_BOSS:
            is_boss = bool(effect_value)
            self.get_data(source_id).is_boss_or_player = is_boss
            if is_boss: self.boss_id = source_id
        elif effect_type == CastingEffect.IS_PLAYER:
            is_player = bool(effect_value)
            self.get_data(source_id).is_boss_or_player = is_player
            if is_player: self.player_id = source_id