from dataclasses import dataclass, field
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
    gcd_duration: int = 0
    cooldown_start: int = -10000
    cooldown_duration: int = 0
    castbar_spell_id: int = Consts.EMPTY_ID
    castbar_start: int = -10000
    castbar_duration: int = 0
    castbar_ticks: int = 0

class CastingSystem:

    VALIDATE_TICKS_READY = "has_channeling_ticks"
    VALIDATE_GCD_READY = "is_gcd_ready"
    VALIDATE_COOLDOWN_READY = "is_cooldown_ready"

    APPLY_TICKS_ADDITION = "add_channeling_ticks"
    APPLY_TICKS_SUBTRACTION = "consume_channeling_ticks"
    APPLY_GCD = "gcd_duration"
    APPLY_COOLDOWN = "base_cooldown"

    def __init__(self) -> None:
        self._data_dct: Dict[int, ObjCastingData] = {}

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, spell_id: int) -> None:
        game_obj = ObjCastingData()
        game_obj.spawn_timestamp = timestamp
        game_obj.spawned_from_spell_id = spell_id
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjCastingData()
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

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> str:
        if validation_type == CastingSystem.VALIDATE_TICKS_READY:
            ticks_remaining = self.get_data(source_id).castbar_ticks
            required_ticks = round(validation_value)
            if ticks_remaining < required_ticks:
                return "out_of_channeling_ticks"
        if validation_type == CastingSystem.VALIDATE_GCD_READY:
            obj_data = self.get_data(source_id)
            gcd_ready_timestamp = obj_data.gcd_start + obj_data.gcd_duration
            if gcd_ready_timestamp > timestamp:
                return "gcd_not_ready"
        if validation_type == CastingSystem.VALIDATE_COOLDOWN_READY:
            obj_data = self.get_data(source_id)
            cooldown_ready_timestamp = obj_data.cooldown_start + obj_data.cooldown_duration
            if cooldown_ready_timestamp > timestamp:
                return "cooldown_not_ready"
        return ""

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, spell_id: int) -> None:
        if effect_type == CastingSystem.APPLY_TICKS_ADDITION:
            self.get_data(source_id).castbar_ticks += round(effect_value)
        elif effect_type == CastingSystem.APPLY_TICKS_SUBTRACTION:
            self.get_data(source_id).castbar_ticks -= max(0, round(effect_value))
        elif effect_type == CastingSystem.APPLY_GCD:
            obj_data = self.get_data(source_id)
            obj_data.gcd_start = timestamp
            obj_data.gcd_duration = round(effect_value)
        elif effect_type == CastingSystem.APPLY_COOLDOWN:
            obj_data = self.get_data(source_id)
            obj_data.cooldown_start = timestamp
            obj_data.cooldown_duration = round(effect_value)