from dataclasses import dataclass, field
from typing import Dict, Iterable

from ._spell_loader import SpellLoader, SpellDef
from .casting_system import CastingSystem
from .health_system import HealthSystem
from .movement_system import MovementSystem
from .targeting_system import TargetingSystem
from .visuals_system import VisualsSystem, ObjVisualsData

@dataclass(slots=True)
class DisplayObj:
    obj_id: int
    pos_xy: tuple[float, float]
    is_visible: bool
    size: float
    color_rgb: tuple[int, int, int]
    sprite_name: str

class StateHandler:
    def __init__(self) -> None:
        self.spell_loader = SpellLoader()
        self.spell_database = self.spell_loader.spell_database

        self._casting_system = CastingSystem()
        self._health_system = HealthSystem()
        self._movement_system = MovementSystem()
        self._targeting_system = TargetingSystem()
        self._visuals_system = VisualsSystem()

    @property
    def environment_id(self) -> int: return self._targeting_system.environment_id
    @property
    def player_id(self) -> int: return self._targeting_system.player_id
    @property
    def active_obj_ids(self) -> set[int]: return set(self._targeting_system.game_obj_data_dct.keys())

    def create_display_obj(self, current_time: int, obj_id: int) -> DisplayObj:
        obj_visuals = self.get_obj_visuals(obj_id)
        pos_xy = self.get_position(obj_id, current_time)
        return DisplayObj(
            obj_id, pos_xy, self.is_visible(obj_id), self.get_size(obj_id),
            (obj_visuals.color_red, obj_visuals.color_green, obj_visuals.color_blue),
            obj_visuals.sprite_name
        )

    def get_spells_for_inputs(self, player_inputs: list[str]) -> list[int]:
        player_spell_id = 42  #Fix this later
        spell_def = self.get_spell_def(player_spell_id)
        return [spell_def.hardware_bindings[i] for i in player_inputs if i in spell_def.hardware_bindings]

    def get_spell_def(self, spell_id: int) -> SpellDef: return self.spell_database[spell_id]
    def get_obj_visuals(self, obj_id: int) -> ObjVisualsData: return self._visuals_system.get_obj_visuals(obj_id)
    def is_visible(self, obj_id: int) -> bool: return self._targeting_system.is_visible(obj_id)
    def get_position(self, obj_id: int, current_time: int) -> tuple[float, float]: return self._movement_system.get_position(obj_id, current_time)
    def get_size(self, obj_id: int) -> float: return self._health_system.get_size(obj_id)
    def get_current_target_for_obj(self, obj_id: int) -> int: return self._targeting_system.get_current_target_for_obj(obj_id)
    def get_ability_timeline(self, spell_id: int) -> dict[int, list[int]]: return self.spell_database[spell_id].timeline if spell_id in self.spell_database else {}

    def is_area_of_effect(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and (spell.flag_aoe_cross_team or spell.flag_aoe_same_team)

    def select_targets_for_aoe(self, source_id: int, spell_id: int) -> Iterable[int]:
        spell = self.spell_database.get(spell_id)
        if not spell: return []
        return self._targeting_system.select_targets_for_aoe(source_id, spell.flag_aoe_cross_team, spell.flag_aoe_same_team)

    def has_channel_start(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and any(e.effect_type == "start_channel" for e in spell.effects)

    def get_spell_ids_for_inputs(self, source_id: int, player_inputs: list[str]) -> Iterable[int]:
        return self._casting_system.get_spell_ids_for_inputs(source_id, player_inputs)

    def is_valid_source(self, source_id: int) -> bool: return self._targeting_system.is_valid_target(source_id)
    def is_valid_target(self, target_id: int) -> bool: return self._targeting_system.is_valid_target(target_id)

    def is_gcd_ready(self, source_id: int, spell_id: int, timestamp: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return self._casting_system.is_gcd_ready(source_id, spell.gcd_mod if spell else 0.0, timestamp)

    def is_cooldown_ready(self, source_id: int, spell_id: int, timestamp: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return self._casting_system.is_cooldown_ready(source_id, spell_id, spell.base_cooldown if spell else 0, timestamp)

    def is_within_range(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return self._movement_system.is_within_range(timestamp, source_id, target_id, spell.range_limit if spell else 0.0)

    def is_obj_spawn(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and any(e.effect_type == "spawn_obj" for e in spell.effects)

    # --- Core Event Logic ---

    def apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        spell = self.spell_database.get(spell_id)
        if not spell: return

        # Base Casting Properties
        if spell.gcd_mod != 0.0: self._casting_system.trigger_gcd(source_id, timestamp, spell.gcd_mod)
        if spell.base_cooldown != 0: self._casting_system.trigger_cooldown(source_id, spell_id, timestamp)

        # Delegate the effect processing to the individual systems
        for effect in spell.effects:
            self._health_system.apply_effect(effect, timestamp, source_id, spell_id, target_id)
            self._movement_system.apply_effect(effect, timestamp, source_id, spell_id, target_id)
            self._targeting_system.apply_effect(effect, timestamp, source_id, spell_id, target_id)
            self._casting_system.apply_effect(effect, timestamp, source_id, spell_id, target_id)
            self._visuals_system.apply_effect(effect, timestamp, source_id, spell_id, target_id)

    def spawn_game_obj(self, timestamp: int, source_id: int, new_obj_id: int, spell_id: int, target_id: int) -> None:
        spell = self.spell_database.get(spell_id)
        if not spell: return

        # Extract the spawn_obj effect to get the spawn parameters
        spawn_effect = next((e for e in spell.effects if e.effect_type == "spawn_obj"), None)
        if not spawn_effect: return

        self._movement_system.spawn_game_obj(timestamp, source_id, new_obj_id, spawn_effect.x_offset, spawn_effect.y_offset, spawn_effect.movespeed)
        self._casting_system.spawn_game_obj(timestamp, new_obj_id, spell.hardware_bindings)
        self._health_system.spawn_game_obj(new_obj_id, spawn_effect.hp)
        self._targeting_system.spawn_game_obj(timestamp, source_id, new_obj_id, target_id, spawn_effect.is_enemy, spawn_effect.is_boss or spawn_effect.is_player, spawn_effect.is_boss, spawn_effect.is_player)
        self._visuals_system.spawn_game_obj(new_obj_id, spawn_effect.color_red, spawn_effect.color_green, spawn_effect.color_blue, spawn_effect.sprite_name)

    def create_environment_obj(self, obj_id: int) -> None:
        self._casting_system.create_environment_obj(obj_id)
        self._health_system.create_environment_obj(obj_id)
        self._movement_system.create_environment_obj(obj_id)
        self._targeting_system.create_environment_obj(obj_id)
        self._visuals_system.create_environment_obj(obj_id)