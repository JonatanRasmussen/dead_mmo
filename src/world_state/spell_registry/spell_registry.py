import yaml
from enum import Enum
from typing import Any
from pathlib import Path
from src.settings import Consts

class SelfcastValidation(str, Enum):
    IS_SOURCE_TARGETING_SELF = Consts.IS_TARGETING_SELF
    IS_TARGET_THE_DESTINATION = Consts.IS_TARGETING_DESTINATION


class SpellRegistry:
    def __init__(self) -> None:
        # Unified ID Registry Data (Shared for both Spells and Assets)
        self._name_to_id: dict[str, int] = {"": 0, Consts.EMPTY_SPELL_NAME: 0}  # Fix later
        self._id_to_name: dict[int, str] = {0: ""}
        self._next_id: int = 1

        # Separated Spell Data Stores
        self.spell_validations: dict[int, dict[str, int]] = {}
        self.spell_effects: dict[int, dict[str, int]] = {}
        self.spell_timelines: dict[int, dict[int, list[int]]] = {}
        self.spell_spawn_as_child: set[int] = set()

    @classmethod
    def initialize_with_loaded_spells(cls, known_effect_types: set[str], known_validation_types: set[str]) -> "SpellRegistry":
        spell_registry = cls()
        valid_validation_types = known_validation_types | {s.value for s in SelfcastValidation}
        valid_effect_types = known_effect_types
        raw_spells = cls._load_spell_config_from_disk()  # Load raw dicts and load them into the spell registry
        spell_registry._parse_and_load(raw_spells, valid_effect_types, valid_validation_types)
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

    def get_effects(self, spell_id: int) -> dict[str, int]:
        return self.spell_effects.get(spell_id, {})

    def get_validations(self, spell_id: int) -> dict[str, int]:
        return self.spell_validations.get(spell_id, {})

    def is_spell_spawning_as_child(self, spell_id: int) -> bool:
        return spell_id in self.spell_spawn_as_child

    def is_spell_targeting_self(self, spell_id: int) -> bool:
        return bool(self.get_validations(spell_id).get(Consts.IS_TARGETING_SELF, False))

    def is_spell_targeting_destination(self, spell_id: int) -> bool:
        return bool(self.get_validations(spell_id).get(Consts.IS_TARGETING_DESTINATION, False))

    def get_timeline_for_spell(self, spell_id: int) -> dict[int, list[int]]:
        return self.spell_timelines.get(spell_id, {})

    def _parse_numeric_dict(self, data: dict[Any, Any], dict_type: str, spell_name: str, known_spells: set[str]) -> dict[str, int]:
        """Parses effects and validations maps strings to floats or handles floats/bools directly."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected '{dict_type}' to be a mapping in spell '{spell_name}'.")
        res: dict[str, int] = {}
        for k, v in data.items():
            if isinstance(v, str):
                # Enforce that string values must be known spells, unless they are specific asset keys
                if k not in ("play_audio", "sprite_id") and v not in known_spells:
                    raise ValueError(f"String value '{v}' for key '{k}' in '{dict_type}' of spell '{spell_name}' must be a known spell name.")
                res[k] = self.get_id(v)
            else:
                res[k] = int(v) if not isinstance(v, bool) else (1 if v else 0)
        return res

    def _parse_and_load(self, raw_spells: dict[Any, Any], valid_effects: set[str], valid_validations: set[str]) -> None:
        """Processes and loads raw loaded dictionaries into the ECS-like memory structues."""
        # Create a definitive set of known spells (including empty constants just in case)
        known_spells = set(raw_spells.keys()) | {"", Consts.EMPTY_SPELL_NAME}

        for spell_name in raw_spells.keys():  # First Pass: Pre-register all spell names to guarantee integer IDs are generated
            self.get_id(spell_name)

        for spell_name, data in raw_spells.items():  # Second Pass: Translate effects, validations, timelines and validate rules
            spell_id = self.get_id(spell_name)

            if data.get("spawn_as_child"):
                self.spell_spawn_as_child.add(spell_id)

            # Pass the known_spells set down to enforce string value rules
            validations = self._parse_numeric_dict(data["validations"], "validations", spell_name, known_spells)
            effects = self._parse_numeric_dict(data["effects"], "effects", spell_name, known_spells)

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

    @staticmethod
    def _load_spell_config_from_disk() -> dict:
        raw_spell_dct: dict = {}
        # Recursively find all .yaml files in data/ and its subdirectories
        for file_path in Path("data").rglob("*.yaml"):
            loaded_spells = SpellRegistry._load_yaml(str(file_path))

            # Replaced `.update()` with an explicit loop to catch duplicate spell names
            for spell_name, spell_data in loaded_spells.items():
                if spell_name in raw_spell_dct:
                    raise ValueError(f"Duplicate spell name detected: '{spell_name}' found in {file_path}, but it was already loaded from another file.")
                raw_spell_dct[spell_name] = spell_data

        return raw_spell_dct

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
            raw_spawn_as_child = s.get("spawn_as_child", False)
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
                "spawn_as_child": raw_spawn_as_child,
                "validations": raw_validations,
                "effects": raw_effects,
                "timeline": timeline
            }
        return normalized_data