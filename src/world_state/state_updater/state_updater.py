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
from ._sfx_system import SfxSystem
from ._vfx_system import VfxSystem, ObjVfxData


class TriggerEffect(str, Enum):
    SPAWN_AS_CHILD = "spawn_as_child"

class SelfcastValidation(str, Enum):
    IS_SELFCAST = "is_selfcast"
    IS_SOURCE_TARGETING_SELF = "is_targeting_self"
    IS_DEST_THE_TARGET = "is_dest_the_target"


class StateUpdater:

    def __init__(self) -> None:

        self._next_obj_id: int = Consts.EMPTY_OBJ_ID + 1
        self._active_game_objs: dict[int, GameObj] = {Consts.EMPTY_OBJ_ID: GameObj()}
        self._systems: list[BaseSystem] = []

        self.casting_system = CastingSystem(self._active_game_objs)
        self._systems.append(self.casting_system)
        self.health_system = HealthSystem(self._active_game_objs)
        self._systems.append(self.health_system)
        self.identity_system = IdentitySystem(self._active_game_objs)
        self._systems.append(self.identity_system)
        self.movement_system = MovementSystem(self._active_game_objs)
        self._systems.append(self.movement_system)
        self.sfx_system = SfxSystem(self._active_game_objs)
        self._systems.append(self.sfx_system)
        self.vfx_system = VfxSystem(self._active_game_objs)
        self._systems.append(self.vfx_system)

    @property
    def active_obj_ids(self) -> Iterable[int]:
        yield from self._active_game_objs

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

        # --- Movement & Position ---
        base_x, base_y = self.movement_system.get_position(obj_id, current_time)

        # --- VFX & Sprites ---
        vfx_data = self.vfx_system.get_read_only_data(obj_id)

        # --- Progress Calculation ---
        progress_amount = 1.0
        if vfx_data.draw_as_cd_bar:
            casting_data = self.casting_system.get_read_only_data(obj_id)
            if casting_data.show_cd_of_parent:
                progress_amount = casting_data.get_cooldown_progress(current_time)
            else:
                parent_casting_data = self.casting_system.get_read_only_data(obj_id)
                progress_amount = parent_casting_data.get_cooldown_progress(current_time)

        actual_width, actual_height, prog_offset_x, prog_offset_y = vfx_data.get_progress_dimensions(progress_amount)
        base_offset_x, base_offset_y = self.vfx_system.get_total_offset(obj_id)

        display_obj.hitbox_xy = (base_x, base_y)
        display_obj.offset_xy = (base_offset_x + prog_offset_x, base_offset_y + prog_offset_y)

        display_obj.is_visible = vfx_data.is_visible
        display_obj.color_rgb = (vfx_data.color_red, vfx_data.color_green, vfx_data.color_blue)
        display_obj.draw_as_square = vfx_data.draw_as_square or vfx_data.draw_as_cd_bar or vfx_data.draw_as_hp_bar
        display_obj.sprite_id = vfx_data.sprite_id
        display_obj.sprite_scale = vfx_data.sprite_scale
        display_obj.sprite_index = vfx_data.get_sprite_index(current_time)
        display_obj.height = actual_height
        display_obj.width = actual_width

        # --- SFX ---
        sfx_data = self.sfx_system.get_read_only_data(obj_id)
        display_obj.audio_id = sfx_data.audio_id
        display_obj.audio_start = sfx_data.audio_start
        display_obj.audio_loop = sfx_data.loop_audio

        return display_obj

    def get_target_for_obj(self, obj_id: int) -> int:
        return self._active_game_objs[obj_id].target_id

    def validate_event(self, timestamp: int, source_id: int, spell_validations: dict[str, int], dest_id: int) -> str:
        for validation_type, validation_value in spell_validations.items():
            for system in self._systems:
                is_valid = system.validate_event(validation_type, validation_value, timestamp, source_id, dest_id)
                if not is_valid:
                    return f"{Consts.FAILED_VALIDATION}_{validation_type}_{validation_value}"
        return ""

    def apply_event(self, timestamp: int, spell_effects: dict[str, int], dest_id: int) -> list[int]:
        triggered_spell_ids: list[int] = []
        for effect_type, effect_value in spell_effects.items():
            for system in self._systems:
                triggered_spell_id = system.apply_effect(effect_type, effect_value, timestamp, dest_id)
                if triggered_spell_id != Consts.EMPTY_SPELL_ID:
                    triggered_spell_ids.append(triggered_spell_id)
        return triggered_spell_ids

    def spawn_game_obj(self, timestamp: int, parent_id: int, spell_id: int, dest_id: int) -> int:
        new_obj_id = self._next_obj_id
        self._next_obj_id += 1
        game_obj = GameObj.create_new(new_obj_id, timestamp, parent_id, spell_id, dest_id)
        self._active_game_objs[new_obj_id] = game_obj
        return new_obj_id