from dataclasses import dataclass, field
from typing import Dict, Iterable
from src.settings import Consts

@dataclass(slots=True)
class ObjCastingData:
    ability_cd_start: dict[int, int] = field(default_factory=dict)
    gcd_start: int = -10000
    gcd_mod: float = 0.0
    channeling_ticks: int = 0
    hardware_bindings: dict[str, int] = field(default_factory=dict)
    current_spell_cast: int = Consts.EMPTY_ID
    cast_start_time: int = 0

    @classmethod
    def create_environment(cls) -> 'ObjCastingData':
        return cls()

    @classmethod
    def create_spawned(cls, timestamp: int) -> 'ObjCastingData':
        return cls(
            ability_cd_start={},
            gcd_start=-10000,
            gcd_mod=0.0,
            hardware_bindings={},
            current_spell_cast=Consts.EMPTY_ID,
            cast_start_time=timestamp,
        )

class CastingSystem:
    def __init__(self) -> None:
        self.game_obj_data_dct: Dict[int, ObjCastingData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjCastingData.create_environment()

    def spawn_game_obj(self, timestamp: int, new_obj_id: int) -> None:
        if new_obj_id in self.game_obj_data_dct: return
        self.game_obj_data_dct[new_obj_id] = ObjCastingData.create_spawned(timestamp)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    # ---- State Update Handlers ----

    def set_hardware_bindings(self, source_id: int, bindings: dict[str, int]) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.hardware_bindings = bindings.copy()

    def trigger_gcd(self, source_id: int, timestamp: int, gcd_mod: float) -> None:
        if source_data := self.game_obj_data_dct.get(source_id):
            source_data.gcd_start = timestamp
            source_data.gcd_mod = gcd_mod

    def trigger_cooldown(self, source_id: int, spell_id: int, timestamp: int) -> None:
        if source_data := self.game_obj_data_dct.get(source_id):
            source_data.ability_cd_start[spell_id] = timestamp

    def modify_channeling_ticks(self, source_id: int, ticks: int) -> None:
        if source_data := self.game_obj_data_dct.get(source_id):
            source_data.channeling_ticks += ticks
            source_data.channeling_ticks = max(0, source_data.channeling_ticks)

    # ---- Cooldown & Input Methods ----

    def get_gcd_progress(self, obj_id: int, gcd_mod: float, current_timestamp: int) -> float:
        if gcd_mod == 0.0: return 1.0
        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or obj_data.gcd_mod == 0.0: return 1.0

        gcd_duration = Consts.BASE_GCD * obj_data.gcd_mod
        if gcd_duration <= 0: return 1.0
        progress = (current_timestamp - obj_data.gcd_start) / gcd_duration
        return min(1.0, max(0.0, progress))

    def is_gcd_ready(self, obj_id: int, gcd_mod: float, current_timestamp: int) -> bool:
        return self.get_gcd_progress(obj_id, gcd_mod, current_timestamp) >= 1.0

    def get_cooldown_progress(self, obj_id: int, spell_id: int, base_cooldown: int, current_timestamp: int) -> float:
        if base_cooldown == 0: return 1.0
        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data: return 1.0

        cd_start = obj_data.ability_cd_start.get(spell_id, -10000)
        progress = (current_timestamp - cd_start) / base_cooldown
        return min(1.0, max(0.0, progress))

    def is_cooldown_ready(self, obj_id: int, spell_id: int, base_cooldown: int, current_timestamp: int) -> bool:
        return self.get_cooldown_progress(obj_id, spell_id, base_cooldown, current_timestamp) >= 1.0

    def is_channeling_continueing(self, obj_id: int, ticks_to_consume: float) -> bool:
        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data: return False
        return obj_data.channeling_ticks >= round(ticks_to_consume)

    def get_spell_ids_for_inputs(self, obj_id: int, hardware_inputs: list[str]) -> Iterable[int]:
        if not hardware_inputs: return
        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.hardware_bindings: return

        for hw_input in hardware_inputs:
            spell_id = obj_data.hardware_bindings.get(hw_input)
            if spell_id is not None and Consts.is_valid_id(spell_id):
                yield spell_id

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if effect_type == "add_channeling_ticks":
            self.modify_channeling_ticks(source_id, round(effect_value))
        elif effect_type == "consume_channeling_ticks":
            self.modify_channeling_ticks(source_id, -round(effect_value))