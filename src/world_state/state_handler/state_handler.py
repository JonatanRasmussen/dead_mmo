from dataclasses import dataclass
from typing import Any, Iterable

from src.settings import Consts
from src.settings import HardwareInputConsts, Icons, Optimizations
from .system_interface import System
from ._yaml_spell_loader import YamlSpellLoader, SpellDef
from ._attachment_system import AttachmentSystem, ObjAttachmentData, AttachmentValidation
from ._casting_system import CastingSystem, ObjCastingData
from ._display_system import DisplaySystem, ObjDisplayData
from ._health_system import HealthSystem, ObjHealthData
from ._identity_system import IdentitySystem
from ._movement_system import MovementSystem, ObjMovementData

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

        self._aura_system = AttachmentSystem()
        self._casting_system = CastingSystem()
        self._display_system = DisplaySystem()
        self._health_system = HealthSystem()
        self._movement_system = MovementSystem()
        self._identity_system = IdentitySystem()

        self._systems: list[System] = [
            self._aura_system,
            self._casting_system,
            self._display_system,
            self._health_system,
            self._movement_system,
            self._identity_system,
        ]

    @property
    def player_id(self) -> int:
        return self._identity_system.player_id

    @property
    def active_obj_ids(self) -> set[int]:
        return set(self._active_game_objs)

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
        return self._identity_system.get_current_target_for_obj(obj_id)

    def has_channel_start(self, spell_id: int) -> bool:
        spell = self.spell_database.get(spell_id)
        return spell is not None and "start_channel" in spell.effects

    def get_spawn_child_id(self, spell_id: int) -> list[int]:
        spell = self.spell_database.get(spell_id)
        return spell.spawn_child if spell is not None else [Consts.EMPTY_ID]

    def get_timeline_for_spell(self, spell_id: int) -> dict[int, list[int]]:
        spell = self.spell_database.get(spell_id)
        return spell.timeline if spell is not None else {}

    def get_aoe_spell_id(self, spell_id: int) -> int:
        spell = self.spell_database.get(spell_id)
        return spell.aoe_spell_id if spell is not None else Consts.EMPTY_ID

    def get_aoe_targets(self, source_id: int, spell_id: int) -> set[int]:
        spell = self.spell_database.get(spell_id)
        if spell is None or spell.spell_id == Consts.EMPTY_ID:  # This should not be possible
            print(f"Warning: spell_id {spell_id} from source_id {source_id} is not in database.")
            return set()
        # For now, target every other obj and let event validation fail on undesired aoe targets
        return self._active_game_objs  # We can optimize this later on

    # --- Core Validation Logic ---
    def validate_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> str:
        spell = self.spell_database.get(spell_id)
        if not spell: return "invalid_spell_id"

        for validation_type, validation_value in spell.validations.items():
            for system in self._systems:
                is_valid = system.validate_event(validation_type, validation_value, timestamp, source_id, target_id)
                if not is_valid:
                    return f"{Consts.FAILED_VALIDATION}_{validation_type}_{validation_value}"
        return ""

    # --- Core Event Logic ---
    def apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        spell = self.spell_database.get(spell_id)
        if not spell: return

        for effect_type, effect_value in spell.effects.items():
            for system in self._systems:
                system.apply_effect(effect_type, effect_value, timestamp, source_id, target_id)

    def spawn_game_obj(self, timestamp: int, parent_id: int, new_obj_id: int, spell_id: int, target_id: int) -> None:
        assert new_obj_id not in self._active_game_objs, "Error: Obj already exists."
        self._active_game_objs.add(new_obj_id)
        for system in self._systems:
            system.spawn_game_obj(timestamp, new_obj_id, parent_id, spell_id, target_id)

    def create_environment_obj(self, obj_id: int) -> None:
        for system in self._systems:
            system.spawn_environment_obj(obj_id)

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