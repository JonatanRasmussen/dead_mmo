import yaml
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from src.settings import Consts
from src.settings.game_input import GameInput


class TriggerEffect(str, Enum):
    SPAWN_AS_CHILD = "spawn_as_child"

class SelfcastValidation(str, Enum):
    IS_SOURCE_TARGETING_SELF = Consts.IS_TARGETING_SELF
    IS_TARGET_THE_DESTINATION = Consts.IS_TARGETING_DESTINATION


@dataclass(slots=True)
class SpellDef:
    spell_id: int = Consts.EMPTY_SPELL_ID
    name: str = Consts.EMPTY_SPELL_NAME
    validations: dict[str, float] = field(default_factory=dict)
    effects: dict[str, float] = field(default_factory=dict)
    timeline: dict[int, list[int]] = field(default_factory=dict)


class SpellRegistry:
    def __init__(self) -> None:
        # Unified ID Registry Data (Shared for both Spells and Assets)
        self._name_to_id: dict[str, int] = {
            "": 0,
            Consts.EMPTY_SPELL_NAME: 0
        }
        self._id_to_name: dict[int, str] = {
            0: ""
        }
        self._next_id: int = 1

        # Separated Spell Data Stores
        self.spell_validations: dict[int, dict[str, float]] = {}
        self.spell_effects: dict[int, dict[str, float]] = {}
        self.spell_timelines: dict[int, dict[int, list[int]]] = {}

    @classmethod
    def initialize_with_loaded_spells(cls, system_effect_types: set[str], system_validation_types: set[str]) -> "SpellRegistry":
        spell_registry = cls()
        valid_validation_types = system_validation_types | {s.value for s in SelfcastValidation}
        valid_effect_types = system_effect_types | {t.value for t in TriggerEffect}
        raw_spells = cls._load_yaml()  # Load raw dicts and load them into the spell registry
        spell_registry._parse_and_load(raw_spells, valid_effect_types, valid_validation_types)
        spell_registry._initialize_input_spells()
        return spell_registry

    def get_id(self, name: str) -> int:
        """Core method to get or generate a unified ID for any string."""
        if name not in self._name_to_id:
            self._name_to_id[name] = self._next_id
            self._id_to_name[self._next_id] = name
            self._next_id += 1
        return self._name_to_id[name]

    def get_name(self, obj_id: float | int) -> str:
        """Core method to get the string associated with a unified ID."""
        int_id = int(obj_id)
        if int_id == 0:
            return ""
        result = self._id_to_name.get(int_id)
        if result is None:
            raise KeyError(f"No string registered for id {int_id}.")
        return result

    def get_spell_id(self, spell_name: str) -> int:
        return self.get_id(spell_name)

    def get_asset_name(self, asset_id: float) -> str:
        return self.get_name(asset_id)

    def get_spell_name(self, spell_id: int) -> str:
        return self._id_to_name.get(spell_id, "unknown_spell")

    def get_effects(self, spell_id: int) -> dict[str, float]:
        return self.spell_effects.get(spell_id, {})

    def get_validations(self, spell_id: int) -> dict[str, float]:
        return self.spell_validations.get(spell_id, {})

    def is_spell_spawning_as_child(self, spell_id: int) -> bool:
        return TriggerEffect.SPAWN_AS_CHILD.value in self.get_effects(spell_id)

    def is_spell_targeting_self(self, spell_id: int) -> bool:
        return bool(self.get_validations(spell_id).get(Consts.IS_TARGETING_SELF, False))

    def is_spell_targeting_destination(self, spell_id: int) -> bool:
        return bool(self.get_validations(spell_id).get(Consts.IS_TARGETING_DESTINATION, False))

    def get_timeline_for_spell(self, spell_id: int) -> dict[int, list[int]]:
        return self.spell_timelines.get(spell_id, {})

    def _parse_numeric_dict(self, data: dict[Any, Any], dict_type: str, spell_name: str) -> dict[str, float]:
        """Parses effects and validations maps strings to floats or handles floats/bools directly."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected '{dict_type}' to be a mapping in spell '{spell_name}'.")
        res = {}
        for k, v in data.items():
            if isinstance(v, str):
                res[k] = float(self.get_id(v))
            else:
                res[k] = float(v) if not isinstance(v, bool) else (1.0 if v else 0.0)
        return res

    def _parse_and_load(self, raw_spells: dict[Any, Any], valid_effects: set[str], valid_validations: set[str]) -> None:
        """Processes and loads raw loaded dictionaries into the ECS-like memory structues."""
        for spell_name in raw_spells.keys():  # First Pass: Pre-register all spell names to guarantee integer IDs are generated
            self.get_id(spell_name)
        for spell_name, data in raw_spells.items():  # Second Pass: Translate effects, validations, timelines and validate rules
            spell_id = self.get_id(spell_name)
            validations = self._parse_numeric_dict(data["validations"], "validations", spell_name)
            effects = self._parse_numeric_dict(data["effects"], "effects", spell_name)
            for validation in validations.keys():
                if validation not in valid_validations:
                    raise ValueError(f"Unknown validation '{validation}' found in spell '{spell_name}'.")
            for effect in effects.keys():  # Validate
                if effect not in valid_effects:
                    raise ValueError(f"Unknown effect '{effect}' found in spell '{spell_name}'.")
            timeline = {}  # Resolve references to other spells inside timelines
            for time_key, spell_names in data["timeline"].items():
                timeline[time_key] = [self.get_id(s) for s in spell_names]
            # Store in separated internal dictionaries
            self.spell_validations[spell_id] = validations
            self.spell_effects[spell_id] = effects
            self.spell_timelines[spell_id] = timeline

    def _initialize_input_spells(self) -> None:
        for spell_id in self._id_to_name:
            assert spell_id >= 0, f"Error: negative spell id {spell_id} found (should be reserved for input_ids)"
        for input_id in GameInput:
            negative_spell_id = int(input_id)
            spell_name = GameInput.create_input_spell_name(negative_spell_id)
            self._name_to_id[spell_name] = negative_spell_id
            self._id_to_name[negative_spell_id] = spell_name
            self.spell_validations[negative_spell_id] = {Consts.IS_BOUND_TO_INPUT_ID: negative_spell_id, Consts.IS_SOURCE_DESTINATION_OF_TARGET: True}
            self.spell_effects[negative_spell_id] = {Consts.TRY_CAST_SELECTED_SPELL: True}
            self.spell_timelines[negative_spell_id] = {}

    @staticmethod
    def _load_yaml(path: str = "data/spells.yaml") -> dict:
        """ Reads the YAML file statically and returns a normalized dictionary.
        Does not maintain any state or handle game logic/IDs. """
        with open(path, "r") as f:
            raw_data = yaml.safe_load(f) or {}
        normalized_data = {}
        for spell_name, s in raw_data.items():
            if s is None:
                s = {}
            # Handle both singular and plural keys gracefully
            raw_validations = s.get("validations", s.get("validation", {}))
            raw_effects = s.get("effects", s.get("effect", {}))
            raw_timeline = s.get("timeline", {})
            if not isinstance(raw_timeline, dict):
                raise ValueError(f"Expected 'timeline' to be a mapping in spell '{spell_name}'.")
            # Standardize timeline payloads into lists
            timeline = {}
            for time_key, val in raw_timeline.items():
                val_list = val if isinstance(val, list) else [val]
                timeline[int(time_key)] = val_list
            normalized_data[spell_name] = {
                "validations": raw_validations,
                "effects": raw_effects,
                "timeline": timeline
            }
        return normalized_data