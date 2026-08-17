from typing import Iterable
from dataclasses import dataclass, field
from enum import IntFlag, auto

from src.settings import Consts
from src.world_state._spell_system import Behavior
from src.world_state._spell_database import SpellDatabase
from ._controls_data import Controls, InputTranslator, KeyPresses, LOADOUT_KEY_TO_INDEX_MAP


class CooldownBehavior(IntFlag):
    """ Various bitflags that define spell cooldown behavior. """
    NONE = 0
    TRIGGER_GCD = auto()
    TRIGGER_COOLDOWN = auto()

    @classmethod
    def from_behavior(cls, behavior: Behavior) -> "CooldownBehavior":
        """Extract the GCD/cooldown-related flags from a Behavior."""
        result = cls.NONE
        for flag in cls:
            if flag is cls.NONE or flag.name is None:
                continue
            source_flag = getattr(Behavior, flag.name, None)
            if source_flag is not None and behavior & source_flag:
                result |= flag
        return result


@dataclass(slots=True)
class SpellCooldownData:
    """Stores the cooldown-relevant template data extracted from a Spell."""
    flags: CooldownBehavior = CooldownBehavior.NONE
    base_gcd: float = 0.0
    base_cooldown: float = 0.0
    spell_bindings: list[int] = field(default_factory=list)
    controls: tuple[Controls, ...] = ()

@dataclass(slots=True)
class ObjCooldownData:
    """ECS-style component storing per-obj cooldown and GCD state."""
    gcd_start: int = -1000
    obj_spawn_timestamp: int = 0
    ability_cd_start: list[int] = field(default_factory=list)
    spell_bindings: list[int] = field(default_factory=list)
    controls: tuple[Controls, ...] = ()


class CooldownSystem:
    def __init__(self, spell_database: SpellDatabase) -> None:
        self._spell_data_dct: dict[int, SpellCooldownData] = self._create_initialized_spell_data_dct(spell_database)
        self.game_obj_data_dct: dict[int, ObjCooldownData] = {}

    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> dict[int, SpellCooldownData]:
        spell_data_dct = {}
        base_gcd = float(getattr(Consts, "BASE_GCD", 0.0))

        for spell in spell_database.get_all_spells():
            spell_bindings: list[int] = []
            controls_tuple: tuple[Controls, ...] = ()

            # Extract configuration from the game_obj loadout, strictly for initial setup.
            if spell.spawned_obj is not None:
                game_obj = spell.spawned_obj.game_obj
                if getattr(game_obj, "_loadout", None) is not None:
                    spell_bindings = list(game_obj._loadout.spell_ids)
                controls_tuple = spell.spawned_obj.obj_controls or ()

            gcd_mod = 1.0  # Room for future GCD modifiers

            spell_data_dct[spell.spell_id] = SpellCooldownData(
                flags=CooldownBehavior.from_behavior(spell.flags),
                base_gcd=base_gcd * gcd_mod,
                base_cooldown=float(getattr(spell, "cooldown", 0.0) or 0.0),
                spell_bindings=spell_bindings,
                controls=controls_tuple,
            )

        return spell_data_dct

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, spell_id: int) -> None:
        template = self._spell_data_dct.get(spell_id)
        if template is None or not template.spell_bindings:
            return
        if new_obj_id in self.game_obj_data_dct:   # idempotent: never double-register
            return

        self.game_obj_data_dct[new_obj_id] = ObjCooldownData(
            gcd_start=-1000,
            obj_spawn_timestamp=timestamp,
            spell_bindings=list(template.spell_bindings),
            ability_cd_start=[Consts.EMPTY_TIMESTAMP] * len(template.spell_bindings),
            controls=template.controls,
        )

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjCooldownData(
            gcd_start=-1000,
            obj_spawn_timestamp=0,
            ability_cd_start=[],
            spell_bindings=[Consts.EMPTY_ID] * len(LOADOUT_KEY_TO_INDEX_MAP),
            controls=()
        )

    def apply_cooldown_event(self, timestamp: int, source_id: int, spell_id: int) -> None:
        """
        Applies a spell's execution behavior to the source's GCD and cooldown tracking.
        """
        spell_data = self._spell_data_dct.get(spell_id)
        if spell_data is None:
            return

        flags = spell_data.flags
        obj_data = self.game_obj_data_dct.get(source_id)

        if obj_data is not None:
            if flags & CooldownBehavior.TRIGGER_GCD:
                obj_data.gcd_start = timestamp
            if flags & CooldownBehavior.TRIGGER_COOLDOWN:
                if spell_id in obj_data.spell_bindings:
                    index = obj_data.spell_bindings.index(spell_id)
                    obj_data.ability_cd_start[index] = timestamp


    def get_gcd_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        """Returns the GCD progress for obj_id casting spell_id. 1.0 means ready.
        Always returns 1.0 if the spell doesn't trigger a GCD."""
        spell_data = self._spell_data_dct.get(spell_id)
        if spell_data is None or not (spell_data.flags & CooldownBehavior.TRIGGER_GCD):
            return 1.0

        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return 1.0

        gcd_duration = spell_data.base_gcd
        if gcd_duration <= 0:
            return 1.0

        progress = (current_timestamp - obj_data.gcd_start) / gcd_duration
        return min(1.0, max(0.0, progress))

    def is_gcd_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        """Checks if obj_id's GCD is finished for spell_id (or if spell_id doesn't use GCD)."""
        return self.get_gcd_progress(obj_id, spell_id, current_timestamp) >= 1.0

    def get_cooldown_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        """Returns the ability cooldown progress for obj_id casting spell_id. 1.0 means ready.
        Always returns 1.0 if the spell doesn't trigger a cooldown."""
        spell_data = self._spell_data_dct.get(spell_id)
        if spell_data is None or not (spell_data.flags & CooldownBehavior.TRIGGER_COOLDOWN):
            return 1.0

        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return 1.0

        if spell_id not in obj_data.spell_bindings:
            return 1.0

        index = obj_data.spell_bindings.index(spell_id)
        cd_duration = spell_data.base_cooldown
        if cd_duration <= 0:
            return 1.0

        cd_start = obj_data.ability_cd_start[index]
        progress = (current_timestamp - cd_start) / cd_duration
        return min(1.0, max(0.0, progress))

    def is_cooldown_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        """Checks if obj_id's cooldown is finished for spell_id (or if spell_id doesn't use a cooldown)."""
        return self.get_cooldown_progress(obj_id, spell_id, current_timestamp) >= 1.0

    def get_spell_ids_for_inputs(self, obj_id: int, hardware_inputs: list[str], timestamp: int) -> Iterable[int]:
        if not hardware_inputs:
            return

        key_presses = InputTranslator.translate_to_keypresses(hardware_inputs)
        if key_presses == KeyPresses.NONE:
            return

        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.spell_bindings:
            return

        # Direct translation without relying on Loadout objects
        for key_flag, index in LOADOUT_KEY_TO_INDEX_MAP.items():
            if key_flag & key_presses:
                spell_id = obj_data.spell_bindings[index]
                if Consts.is_valid_id(spell_id):
                    yield spell_id

    def get_scripted_spells(self, obj_id: int, spawn_timestamp: int) -> Iterable[tuple[int, int, int]]:
        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.controls or not obj_data.spell_bindings:
            return

        for original_controls in obj_data.controls:
            # Create a copy and apply the offset
            controls = original_controls.create_copy()
            controls.increase_offset(spawn_timestamp)

            priority = 0
            for key_flag, index in LOADOUT_KEY_TO_INDEX_MAP.items():
                if key_flag in controls.key_presses:
                    spell_id = obj_data.spell_bindings[index]
                    if Consts.is_valid_id(spell_id):
                        priority += 1
                        yield spell_id, controls.ingame_time, priority
