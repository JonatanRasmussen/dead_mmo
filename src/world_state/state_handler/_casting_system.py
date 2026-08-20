from dataclasses import dataclass, field
from typing import Dict, Iterable
from enum import IntFlag, auto

from src.settings import Consts


class CastingBehavior(IntFlag):
    NONE = 0
    TRIGGER_GCD = auto()
    TRIGGER_COOLDOWN = auto()
    DENY_IF_CASTING = auto()
    START_CHANNEL = auto()
    STOP_CHANNEL = auto()


@dataclass(slots=True)
class SpellCastingData:
    flags: CastingBehavior = CastingBehavior.NONE
    timeline: dict[int, list[int]] = field(default_factory=dict)
    base_cooldown: float = 0.0
    hardware_bindings: dict[str, int] = field(default_factory=dict)
    gcd_mod: float = 1.0
    channel_duration: int = field(init=False, default=0)

    def __post_init__(self):
        # Infer how long this channel lasts by the final timestamp in its timeline
        self.channel_duration = max(self.timeline.keys()) if self.timeline else 0


@dataclass(slots=True)
class ObjCastingData:
    ability_cd_start: dict[int, int] = field(default_factory=dict)
    gcd_start: int = -10000
    gcd_mod: float = 1.0
    hardware_bindings: dict[str, int] = field(default_factory=dict)
    current_spell_cast: int = Consts.EMPTY_ID
    cast_start_time: int = 0

    @classmethod
    def create_environment(cls) -> 'ObjCastingData':
        return cls()

    @classmethod
    def create_from_spell(cls, timestamp: int, spell_data: SpellCastingData) -> 'ObjCastingData':
        return cls(
            ability_cd_start={},
            gcd_start=-10000,
            gcd_mod=spell_data.gcd_mod,
            hardware_bindings=spell_data.hardware_bindings.copy() if spell_data.hardware_bindings else {},
            current_spell_cast=Consts.EMPTY_ID,
            cast_start_time=timestamp,
        )


class CastingSystem:
    def __init__(self, spell_data_dct: Dict[int, SpellCastingData]) -> None:
        self.spell_data_dct: Dict[int, SpellCastingData] = spell_data_dct
        self.game_obj_data_dct: Dict[int, ObjCastingData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjCastingData.create_environment()

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, spell_id: int) -> None:
        if spell_id not in self.spell_data_dct or new_obj_id in self.game_obj_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        self.game_obj_data_dct[new_obj_id] = ObjCastingData.create_from_spell(timestamp, spell_data)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    def apply_casting_event(self, timestamp: int, source_id: int, spell_id: int) -> None:
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_data_dct.get(source_id)

        if source_data:
            if flags & CastingBehavior.TRIGGER_GCD:
                source_data.gcd_start = timestamp
            if flags & CastingBehavior.TRIGGER_COOLDOWN:
                source_data.ability_cd_start[spell_id] = timestamp
            if flags & CastingBehavior.START_CHANNEL:
                source_data.cast_start_time = timestamp
                source_data.current_spell_cast = spell_id
            if flags & CastingBehavior.STOP_CHANNEL:
                source_data.cast_start_time = timestamp
                source_data.current_spell_cast = Consts.EMPTY_ID

    # ---- Cooldown & Input Methods ----

    def get_gcd_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        spell_data = self.spell_data_dct.get(spell_id)
        if spell_data is None or not (spell_data.flags & CastingBehavior.TRIGGER_GCD):
            return 1.0

        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return 1.0

        base_gcd = float(getattr(Consts, "BASE_GCD", 0.0))
        gcd_duration = base_gcd * obj_data.gcd_mod
        if gcd_duration <= 0:
            return 1.0

        progress = (current_timestamp - obj_data.gcd_start) / gcd_duration
        return min(1.0, max(0.0, progress))

    def is_gcd_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        return self.get_gcd_progress(obj_id, spell_id, current_timestamp) >= 1.0

    def get_cooldown_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        spell_data = self.spell_data_dct.get(spell_id)
        if spell_data is None or not (spell_data.flags & CastingBehavior.TRIGGER_COOLDOWN):
            return 1.0

        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return 1.0

        cd_duration = spell_data.base_cooldown
        if cd_duration <= 0:
            return 1.0

        cd_start = obj_data.ability_cd_start.get(spell_id, -10000)
        progress = (current_timestamp - cd_start) / cd_duration
        return min(1.0, max(0.0, progress))

    def is_cooldown_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        return self.get_cooldown_progress(obj_id, spell_id, current_timestamp) >= 1.0

    def get_spell_ids_for_inputs(self, obj_id: int, hardware_inputs: list[str]) -> Iterable[int]:
        if not hardware_inputs:
            return

        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.hardware_bindings:
            return

        for hw_input in hardware_inputs:
            spell_id = obj_data.hardware_bindings.get(hw_input)
            if spell_id is not None and Consts.is_valid_id(spell_id):
                yield spell_id

    # ---- Timeline properties ----

    def has_channel_start(self, spell_id: int) -> bool:
        return bool(self.spell_data_dct[spell_id].flags & CastingBehavior.START_CHANNEL)

    def get_ability_timeline(self, spell_id: int) -> dict[int, list[int]]:
        return self.spell_data_dct[spell_id].timeline

    def is_aura_active(self, current_timestamp: int, obj_id: int, spell_id: int) -> bool:
        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return False
        spell_data = self.spell_data_dct.get(spell_id)

        # Check against inferred duration
        if spell_data and current_timestamp > (obj_data.cast_start_time + spell_data.channel_duration):
            return False

        if obj_data.current_spell_cast != spell_id:
            return False
        return True