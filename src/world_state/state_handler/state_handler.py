from dataclasses import dataclass
from typing import Iterable

from src.settings import HardwareInputConsts, Icons
from ._yaml_spell_loader import YamlSpellLoader, SpellDef
from ._aura_system import AuraSystem, ObjAuraData
from ._casting_system import CastingSystem, ObjCastingData
from ._display_system import DisplaySystem, ObjDisplayData
from ._health_system import HealthSystem, ObjHealthData
from ._movement_system import MovementSystem, ObjMovementData
from ._targeting_system import TargetingSystem, ObjTargetingData

@dataclass(slots=True)
class DisplayObj:
    obj_id: int
    pos_xy: tuple[float, float]
    is_visible: bool
    size: float
    color_rgb: tuple[int, int, int]
    sprite_name: str

@dataclass(slots=True)
class DisplaySpell:
    spell_id: int
    audio_name: str
    animation_name: str
    animation_scale: float

class StateHandler:
    def __init__(self) -> None:
        self.spell_loader = YamlSpellLoader()
        self.spell_database = self.spell_loader.spell_database
        self._active_game_objs: set = set()
        self._aura_system = AuraSystem()
        self._casting_system = CastingSystem()
        self._display_system = DisplaySystem()
        self._health_system = HealthSystem()
        self._movement_system = MovementSystem()
        self._targeting_system = TargetingSystem()

    @property
    def player_id(self) -> int:
        return self._targeting_system.player_id

    @property
    def active_obj_ids(self) -> set[int]:
        return set(self._targeting_system._data_dct.keys())

    def create_display_obj(self, current_time: int, obj_id: int) -> DisplayObj:
        obj_display = self.get_obj_display_data(obj_id)
        pos_xy = self.get_position(obj_id, current_time)
        return DisplayObj(
            obj_id, pos_xy, obj_display.is_visible, self.get_size(obj_id),
            (obj_display.color_red, obj_display.color_green, obj_display.color_blue),
            Icons.get_icon_name(obj_display.icon_id)
        )

    def create_display_spell(self, spell_id: int) -> DisplaySpell | None:
        spell = self.spell_database.get(spell_id)
        if not spell: return None
        return DisplaySpell(
            spell_id=spell_id,
            audio_name=spell.cosmetics.get("audio_name", ""),
            animation_name=spell.cosmetics.get("animation_name", ""),
            animation_scale=spell.animation_scale
        )

    def get_spell_def(self, spell_id: int) -> SpellDef:
        return self.spell_database[spell_id]

    def get_obj_health_data(self, obj_id: int) -> ObjHealthData:
        return self._health_system.get_data(obj_id)

    def get_obj_display_data(self, obj_id: int) -> ObjDisplayData:
        return self._display_system.get_data(obj_id)

    def is_visible(self, obj_id: int) -> bool:
        return self._display_system.is_visible(obj_id)

    def get_position(self, obj_id: int, current_time: int) -> tuple[float, float]:
        return self._movement_system.get_position(obj_id, current_time)

    def get_size(self, obj_id: int) -> float:
        return self._health_system.get_size(obj_id)

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self._targeting_system.get_current_target_for_obj(obj_id)

    def select_targets_for_aoe(self, source_id: int, cross_team: bool, same_team: bool) -> Iterable[int]:
        return self._targeting_system.select_targets_for_aoe(source_id, cross_team, same_team)

    def has_channel_start(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and "start_channel" in spell.effects

    # --- Core Validation Logic ---
    def validate_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> str:
        spell = self.spell_database.get(spell_id)
        if not spell: return "invalid_spell_id"

        for validation_type, validation_value in spell.validations.items():
            if err := self._aura_system.validate_event(validation_type, validation_value, source_id, target_id): return err
            if err := self._casting_system.validate_event(validation_type, validation_value, timestamp, source_id): return err
            if err := self._display_system.validate_event(): return err
            if err := self._health_system.validate_event(): return err
            if err := self._movement_system.validate_event(validation_type, validation_value, timestamp, source_id, target_id): return err
            if err := self._targeting_system.validate_event(validation_type, source_id, target_id): return err
        return ""

    # --- Core Event Logic ---
    def apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        spell = self.spell_database.get(spell_id)
        if not spell: return

        for effect_type, effect_value in spell.effects.items():
            self._aura_system.apply_effect(effect_type, source_id, target_id)
            self._casting_system.apply_effect(effect_type, effect_value, timestamp, source_id)
            self._display_system.apply_effect(effect_type, effect_value, source_id)
            self._health_system.apply_effect(effect_type, effect_value, source_id, target_id)
            self._movement_system.apply_effect(effect_type, effect_value, timestamp, source_id, target_id)
            self._targeting_system.apply_effect(effect_type, effect_value, source_id, target_id)

    def spawn_game_obj(self, timestamp: int, parent_id: int, new_obj_id: int, spell_id: int, target_id: int) -> None:
        assert new_obj_id not in self._active_game_objs, "Error: Obj already exists."
        self._active_game_objs.add(new_obj_id)
        self._aura_system.spawn_game_obj(new_obj_id, parent_id, spell_id)
        self._casting_system.spawn_game_obj(new_obj_id, parent_id)
        self._display_system.spawn_game_obj(new_obj_id)
        self._health_system.spawn_game_obj(new_obj_id)
        self._movement_system.spawn_game_obj(timestamp, new_obj_id, parent_id)
        self._targeting_system.spawn_game_obj(new_obj_id, parent_id, target_id)

    def create_environment_obj(self, obj_id: int) -> None:
        self._targeting_system.spawn_environment_obj(obj_id)
        self._casting_system.spawn_environment_obj(obj_id)
        self._health_system.spawn_environment_obj(obj_id)
        self._movement_system.spawn_environment_obj(obj_id)
        self._display_system.spawn_environment_obj(obj_id)
        self._aura_system.spawn_environment_obj(obj_id)

    def get_spells_for_player_inputs(self, player_inputs: list[str]) -> list[int]:
        spell_ids = []
        for player_input in player_inputs:
            match player_input:
                case HardwareInputConsts.KEYBOARD_KEYDOWN_1: spell_ids.append(128)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_2: spell_ids.append(911)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_3: spell_ids.append(171)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_4: spell_ids.append(1440)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: spell_ids.append(15)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: spell_ids.append(91)
                case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: spell_ids.append(92)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: spell_ids.append(181)
                case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: spell_ids.append(182)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: spell_ids.append(271)
                case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: spell_ids.append(272)
                case HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: spell_ids.append(1)
                case HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: spell_ids.append(2)
        return spell_ids