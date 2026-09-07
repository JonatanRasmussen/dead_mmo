from typing import Iterable
from dataclasses import dataclass
from src.settings import HardwareInputConsts

from ._spell_loader import SpellLoader
from .casting_system import CastingSystem
from .health_system import HealthSystem
from .movement_system import MovementSystem
from .targeting_system import TargetingSystem
from .visuals_system import VisualsSystem, SpellVisualsData, ObjVisualsData


@dataclass(slots=True)
class DisplayObj:
    obj_id: int
    pos_xy: tuple[float, float]
    is_visible: bool
    size: float
    color_rgb: tuple[int, int, int]
    sprite_name: str


class InputRegistry:
    """ Maps hardware input strings directly to Spell IDs """
    BINDINGS = {
        HardwareInputConsts.KEYBOARD_KEYDOWN_1: 128,
        HardwareInputConsts.KEYBOARD_KEYDOWN_2: 113,
        HardwareInputConsts.KEYBOARD_KEYDOWN_3: 171,
        HardwareInputConsts.KEYBOARD_KEYDOWN_4: 124,
        HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: 15,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: 91,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: 92,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: 181,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: 182,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: 271,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: 272,
        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: 1,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: 2,
    }

    @classmethod
    def get_spells_for_inputs(cls, player_inputs: list[str]) -> list[int]:
        """ Returns a list of Spell IDs corresponding to the active inputs. """
        return [cls.BINDINGS[i] for i in player_inputs if i in cls.BINDINGS]


class StateHandler:
    """ Encapsulates all ECS-like systems and exposes a unified interface. """

    def __init__(self) -> None:
        self.spell_loader: SpellLoader = SpellLoader()
        self._casting_system: CastingSystem = self.spell_loader.create_casting_system()
        self._health_system: HealthSystem = self.spell_loader.create_health_system()
        self._movement_system: MovementSystem = self.spell_loader.create_movement_system()
        self._targeting_system: TargetingSystem = self.spell_loader.create_targeting_system()
        self._visuals_system: VisualsSystem = self.spell_loader.create_visuals_system()

    @property
    def environment_id(self) -> int:
        return self._targeting_system.environment_id

    @property
    def player_id(self) -> int:
        return self._targeting_system.player_id

    @property
    def active_obj_ids(self) -> set[int]:
        return set(self._targeting_system.game_obj_data_dct.keys())

    def create_display_obj(self, current_time: int, obj_id: int) -> DisplayObj:
        obj_visuals = self.get_obj_visuals(obj_id)
        pos_xy = self.get_position(obj_id, current_time)
        is_visible = self.is_visible(obj_id)
        size = self.get_size(obj_id)
        color_rgb = (obj_visuals.color_red, obj_visuals.color_green, obj_visuals.color_blue)
        sprite_name = obj_visuals.sprite_name
        return DisplayObj(obj_id, pos_xy, is_visible, size, color_rgb, sprite_name)

    def get_all_obj_ids(self) -> Iterable[int]:
        return self._targeting_system.game_obj_data_dct.keys()

    def get_obj_visuals(self, obj_id: int) -> ObjVisualsData:
        return self._visuals_system.get_obj_visuals(obj_id)

    def is_visible(self, obj_id: int) -> bool:
        return self._targeting_system.is_visible(obj_id)

    def get_position(self, obj_id: int, current_time: int) -> tuple[float, float]:
        return self._movement_system.get_position(obj_id, current_time)

    def get_size(self, obj_id: int) -> float:
        return self._health_system.get_size(obj_id)

    def get_spell_visuals(self, spell_id: int) -> SpellVisualsData:
        return self._visuals_system.get_spell_visuals(spell_id)

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self._targeting_system.get_current_target_for_obj(obj_id)

    def get_ability_timeline(self, spell_id: int) -> dict[int, list[int]]:
        return self._casting_system.get_ability_timeline(spell_id)

    def is_area_of_effect(self, spell_id: int) -> bool:
        return self._targeting_system.is_area_of_effect(spell_id)

    def select_targets_for_aoe(self, source_id: int, target_id: int) -> Iterable[int]:
        return self._targeting_system.select_targets_for_aoe(source_id, target_id)

    def has_channel_start(self, spell_id: int) -> bool:
        return self._casting_system.has_channel_start(spell_id)

    def get_spell_ids_for_inputs(self, source_id: int, player_inputs: list[str]) -> Iterable[int]:
        return self._casting_system.get_spell_ids_for_inputs(source_id, player_inputs)

    def is_valid_source(self, source_id: int) -> bool:
        return self._targeting_system.is_valid_target(source_id)

    def is_gcd_ready(self, source_id: int, spell_id: int, timestamp: int) -> bool:
        return self._casting_system.is_gcd_ready(source_id, spell_id, timestamp)

    def is_cooldown_ready(self, source_id: int, spell_id: int, timestamp: int) -> bool:
        return self._casting_system.is_cooldown_ready(source_id, spell_id, timestamp)

    def is_valid_target(self, target_id: int) -> bool:
        return self._targeting_system.is_valid_target(target_id)

    def is_within_range(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> bool:
        return self._movement_system.is_within_range(timestamp, source_id, spell_id, target_id)

    def is_obj_spawn(self, spell_id: int) -> bool:
        return self._targeting_system.is_obj_spawn(spell_id)

    def apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        self._casting_system.apply_casting_event(timestamp, source_id, spell_id)
        self._health_system.apply_health_event(source_id, spell_id, target_id)
        self._movement_system.apply_movement_event(timestamp, source_id, spell_id, target_id)
        self._targeting_system.apply_targeting_event(source_id, spell_id, target_id)
        self._visuals_system.apply_visuals_event(source_id, spell_id)

    def spawn_game_obj(self, timestamp: int, source_id: int, new_obj_id: int, spell_id: int, target_id: int) -> None:
        self._movement_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id)
        self._casting_system.spawn_game_obj(timestamp, new_obj_id, spell_id)
        self._health_system.spawn_game_obj(new_obj_id, spell_id)
        self._targeting_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
        self._visuals_system.spawn_game_obj(new_obj_id, spell_id)

    def create_environment_obj(self, obj_id: int) -> None:
        self._casting_system.create_environment_obj(obj_id)
        self._health_system.create_environment_obj(obj_id)
        self._movement_system.create_environment_obj(obj_id)
        self._targeting_system.create_environment_obj(obj_id)
        self._visuals_system.create_environment_obj(obj_id)