from typing import Iterable
from enum import Enum
from src.settings import Consts
from .display_obj import DisplayObj
from .game_obj import GameObj
from .base_system import BaseSystem
from ._casting_system import CastingSystem, ObjCastingData
from ._health_system import HealthSystem, ObjHealthData
from ._identity_system import IdentitySystem
from ._movement_system import MovementSystem, ObjMovementData
from ._offset_system import OffsetSystem
from ._periodic_system import PeriodicSystem
from ._sfx_system import SfxSystem
from ._vfx_system import VfxSystem, ObjVfxData
from ._visibility_system import VisibilitySystem


class TriggerEffect(str, Enum):
    SPAWN_AS_CHILD = "spawn_as_child"

class SelfcastValidation(str, Enum):
    IS_SELFCAST = "is_selfcast"
    IS_SOURCE_TARGETING_SELF = "is_targeting_self"
    IS_TARGET_THE_DESTINATION = "is_target_the_destination"


class StateUpdater:
    def __init__(self) -> None:
        self._next_obj_id: int = Consts.EMPTY_OBJ_ID + 1
        self._active_game_objs: dict[int, GameObj] = {Consts.EMPTY_OBJ_ID: GameObj()}
        self._systems: list[BaseSystem] = StateUpdater._initialize_list_of_systems(self._active_game_objs)

    @property
    def active_obj_ids(self) -> Iterable[int]:
        yield from self._active_game_objs

    @staticmethod
    def _initialize_list_of_systems(game_objs: dict[int, GameObj]) -> list[BaseSystem]:
        return [
            CastingSystem(game_objs),
            HealthSystem(game_objs),
            IdentitySystem(game_objs),
            MovementSystem(game_objs),
            OffsetSystem(game_objs),
            PeriodicSystem(game_objs),
            SfxSystem(game_objs),
            VfxSystem(game_objs),
            VisibilitySystem(game_objs),
        ]

    def get_effects_known_to_systems(self) -> set[str]:
        valid_effects: set[str] = {t.value for t in TriggerEffect}
        for system in self._systems:
            valid_effects.update(system.get_effect_types())
        return valid_effects

    def get_validations_known_to_systems(self) -> set[str]:
        valid_validations: set[str] = {s.value for s in SelfcastValidation}
        for system in self._systems:
            valid_validations.update(system.get_validation_types())
        return valid_validations

    def create_display_obj(self, current_time: int, obj_id: int) -> DisplayObj:
        display_obj = DisplayObj(obj_id=obj_id)
        for system in self._systems:
            display_obj = system.build_display_obj(current_time, obj_id, display_obj)
        return display_obj

    def get_destination_for_obj(self, obj_id: int) -> int:
        return self._active_game_objs[obj_id].destination_id

    def validate_event(self, timestamp: int, source_id: int, spell_validations: dict[str, int], target_id: int) -> str:
        for validation_type, validation_value in spell_validations.items():
            for system in self._systems:
                is_valid = system.validate_event(validation_type, validation_value, timestamp, source_id, target_id)
                if not is_valid:
                    return f"{Consts.FAILED_VALIDATION}_{validation_type}_{validation_value}"
        return ""

    def apply_event(self, timestamp: int, spell_effects: dict[str, int], target_id: int) -> list[int]:
        triggered_spell_ids: list[int] = []
        for effect_type, effect_value in spell_effects.items():
            for system in self._systems:
                triggered_spell_id = system.apply_effect(effect_type, effect_value, timestamp, target_id)
                if triggered_spell_id != Consts.EMPTY_SPELL_ID:
                    triggered_spell_ids.append(triggered_spell_id)
        return triggered_spell_ids

    def spawn_game_obj(self, timestamp: int, parent_id: int, spell_id: int, target_id: int) -> int:
        new_obj_id = self._next_obj_id
        self._next_obj_id += 1
        game_obj = GameObj.create_new(new_obj_id, timestamp, parent_id, spell_id, target_id)
        self._active_game_objs[new_obj_id] = game_obj
        return new_obj_id