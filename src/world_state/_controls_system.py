'''
import copy
from typing import Iterable, Optional
from dataclasses import dataclass
from enum import IntFlag, auto

from src.settings import Consts
from src.world_state import Behavior
from ._controls_data import Controls, InputTranslator, KeyPresses, Loadout, LOADOUT_KEY_TO_INDEX_MAP
from ._spell_database import SpellDatabase


class ControlsBehavior(IntFlag):
    """ Various bitflags that define controls-relevant spell behavior. """
    NONE = 0
    TRIGGER_GCD = auto()
    TRIGGER_COOLDOWN = auto()

    @classmethod
    def from_behavior(cls, behavior: Behavior) -> "ControlsBehavior":
        result = cls.NONE
        for flag in cls:
            if flag is cls.NONE or flag.name is None:
                continue
            source_flag = getattr(Behavior, flag.name, None)   # tolerate missing flags
            if source_flag is not None and behavior & source_flag:
                result |= flag
        return result


@dataclass(slots=True)
class SpellControlsData:
    """Stores the controls-relevant template data extracted from a Spell.

    loadout/controls act as blueprints only: loadout is deep-copied per obj_id
    on spawn so each instance gets independent GCD/cooldown state.
    """
    flags: ControlsBehavior = ControlsBehavior.NONE
    base_gcd: float = 0.0
    base_cooldown: float = 0.0
    loadout: Optional[Loadout] = None
    controls: tuple[Controls, ...] = ()


@dataclass(slots=True)
class ObjControlsData:
    """ECS-style component storing per-obj controls state (independent Loadout)."""
    loadout: Loadout
    controls: tuple[Controls, ...] = ()


class ControlsSystem:
    # Legacy path shared the template's Loadout object; keep that for snapshot parity.
    INDEPENDENT_LOADOUT_PER_OBJ = True
    def __init__(self, spell_database: SpellDatabase) -> None:
        self._templates: dict[int, SpellControlsData] = ControlsSystem._create_initialized_spell_data_dct(spell_database)
        self.game_obj_controls_dct: dict[int, ObjControlsData] = {}
    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> dict[int, SpellControlsData]:
        templates = {}
        base_gcd = float(getattr(Consts, "BASE_GCD", 0.0))
        for spell in spell_database.get_all_spells():
            loadout = None
            controls_tuple: tuple[Controls, ...] = ()
            if spell.spawned_obj is not None:
                game_obj = spell.spawned_obj.game_obj
                loadout = game_obj._loadout
                controls_tuple = spell.spawned_obj.obj_controls or ()
            gcd_mod = 1.0
            templates[spell.spell_id] = SpellControlsData(
                flags=ControlsBehavior.from_behavior(spell.flags),
                base_gcd=base_gcd * gcd_mod,
                base_cooldown=float(getattr(spell, "cooldown", 0.0) or 0.0),
                loadout=loadout,
                controls=controls_tuple,
            )
        return templates

    def spawn_game_obj(self, new_obj_id: int, spell_id: int) -> None:
        template = self._templates.get(spell_id)
        if template is None or template.loadout is None:
            return
        if new_obj_id in self.game_obj_controls_dct:   # idempotent: never double-register
            return
        new_loadout = template.loadout.copy() if ControlsSystem.INDEPENDENT_LOADOUT_PER_OBJ else template.loadout
        self.game_obj_controls_dct[new_obj_id] = ObjControlsData(
            loadout=new_loadout,
            controls=template.controls,
        )

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_controls_dct.pop(obj_id, None)

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_controls_dct[obj_id] = ObjControlsData(
            loadout=Loadout(),
            controls=()
        )

    def apply_controls_event(self, timestamp: int, source_id: int, spell_id: int) -> None:
        """
        Applies a spell's controls behavior (GCD/cooldown tracking, spawn/despawn) to objects.
        """
        spell_data = self._templates.get(spell_id)
        if spell_data is None:
            return
        flags = spell_data.flags

        controls_data = self.game_obj_controls_dct.get(source_id)
        if controls_data is not None:
            if flags & ControlsBehavior.TRIGGER_GCD:
                controls_data.loadout.gcd_start = timestamp
            if flags & ControlsBehavior.TRIGGER_COOLDOWN:
                loadout = controls_data.loadout
                cd_list = getattr(loadout, "ability_cd_start", None) or getattr(loadout, "ability_cds", None)
                if cd_list is not None and spell_id in loadout.spell_ids:
                    cd_list[loadout.spell_ids.index(spell_id)] = timestamp

    def get_spell_ids_for_inputs(self, obj_id: int, hardware_inputs: list[str], timestamp: int) -> Iterable[int]:
        if not hardware_inputs:
            yield from []
            return
        key_presses = InputTranslator.translate_to_keypresses(hardware_inputs)
        if key_presses == KeyPresses.NONE:
            yield from []
            return
        controls_data = self.game_obj_controls_dct.get(obj_id)
        if not controls_data:
            yield from []
        else:
            controls = Controls(obj_id=obj_id, timeline_timestamp=timestamp, key_presses=key_presses)
            yield from controls_data.loadout.convert_controls_to_spell_ids(controls, obj_id)

    def get_scripted_spells(self, obj_id: int, spawn_timestamp: int) -> Iterable[tuple[int, int, int]]:
        controls_data = self.game_obj_controls_dct.get(obj_id)
        if not controls_data or not controls_data.controls:
            return

        for original_controls in controls_data.controls:
            # Create a copy and apply the offset, just like the old system
            controls = original_controls.create_copy()
            controls.increase_offset(spawn_timestamp)

            priority = 0
            for spell_id in controls_data.loadout.convert_controls_to_spell_ids(controls, obj_id):
                priority += 1
                yield spell_id, controls.ingame_time, priority

    def get_gcd_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        """Returns the GCD progress for obj_id casting spell_id. 1.0 means ready.
        Always returns 1.0 if the spell doesn't trigger a GCD."""
        spell_data = self._templates.get(spell_id)
        if spell_data is None or not (spell_data.flags & ControlsBehavior.TRIGGER_GCD):
            return 1.0
        controls_data = self.game_obj_controls_dct.get(obj_id)
        if controls_data is None:
            return 1.0
        gcd_duration = spell_data.base_gcd
        if gcd_duration <= 0:
            return 1.0
        progress = (current_timestamp - controls_data.loadout.gcd_start) / gcd_duration
        return min(1.0, max(0.0, progress))

    def is_gcd_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        """Checks if obj_id's GCD is finished for spell_id (or if spell_id doesn't use GCD)."""
        return self.get_gcd_progress(obj_id, spell_id, current_timestamp) >= 1.0

    def get_cooldown_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        """Returns the ability cooldown progress for obj_id casting spell_id. 1.0 means ready.
        Always returns 1.0 if the spell doesn't trigger a cooldown."""
        spell_data = self._templates.get(spell_id)
        if spell_data is None or not (spell_data.flags & ControlsBehavior.TRIGGER_COOLDOWN):
            return 1.0
        controls_data = self.game_obj_controls_dct.get(obj_id)
        if controls_data is None:
            return 1.0
        loadout = controls_data.loadout
        if spell_id not in loadout.spell_ids:
            return 1.0
        index = loadout.spell_ids.index(spell_id)
        cd_duration = spell_data.base_cooldown
        if cd_duration <= 0:
            return 1.0
        cd_start = loadout.ability_cd_start[index]
        progress = (current_timestamp - cd_start) / cd_duration
        return min(1.0, max(0.0, progress))

    def is_cooldown_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        """Checks if obj_id's cooldown is finished for spell_id (or if spell_id doesn't use a cooldown)."""
        return self.get_cooldown_progress(obj_id, spell_id, current_timestamp) >= 1.0
'''