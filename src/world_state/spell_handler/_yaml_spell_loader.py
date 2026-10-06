import yaml
from enum import Enum
from typing import Dict

from src.settings import Consts
from .spell_def import SpellDef


class TriggerType(str, Enum):
    TIMELINE = "timeline"

VALID_TRIGGER_TYPES = {t.value for t in TriggerType}

class TriggerEffect(str, Enum):
    SPAWN_AS_CHILD = "spawn_as_child"

class SelfcastValidation(str, Enum):
    IS_SOURCE_TARGETING_SELF = Consts.IS_TARGETING_SELF
    IS_TARGET_THE_DESTINATION = Consts.IS_TARGETING_DESTINATION

class RegistryForAssetIDs:
    def __init__(self) -> None:
        self._asset_name_to_id: dict[str, float] = {}
        self._asset_id_to_name: dict[float, str] = {}
        self._next_id: int = 1  # 0 reserved for Consts.EMPTY_ID / "no value"

    def register_asset_name(self, asset_name: str) -> float:
        existing = self._asset_name_to_id.get(asset_name)
        if existing is not None:
            return existing
        asset_id = float(self._next_id)
        self._next_id += 1
        self._asset_name_to_id[asset_name] = asset_id
        self._asset_id_to_name[asset_id] = asset_name
        return asset_id

    def get_asset_name(self, asset_id: float) -> str:
        if int(asset_id) == Consts.EMPTY_ASSET_ID:
            return ""
        result = self._asset_id_to_name.get(asset_id)
        if result is None:
            raise KeyError(f"No string registered for asset_id {asset_id}.")
        return result


class YamlSpellLoader:
    def __init__(self, yaml_path: str = "data/spells.yaml") -> None:
        self.asset_id_registry = RegistryForAssetIDs()

        # Map empty_spell to 0 (Consts.EMPTY_SPELL_ID) by default
        self.spell_name_to_id: dict[str, int] = {"empty_spell": Consts.EMPTY_SPELL_ID}
        self._next_spell_id: int = 1

        self.spell_database: dict[int, SpellDef] = self._load_yaml(yaml_path)

    def get_spell_id(self, spell_name: str) -> int:
        """Returns the integer ID for a spell name, generating one if it doesn't exist."""
        if spell_name not in self.spell_name_to_id:
            self.spell_name_to_id[spell_name] = self._next_spell_id
            self._next_spell_id += 1
        return self.spell_name_to_id[spell_name]

    def validate_types(self, valid_effect_types: set[str], valid_validation_types: set[str]) -> None:
        """Called externally after loading to ensure all parsed keys are valid."""
        for _spell_id, spell in self.spell_database.items():
            for effect in spell.effects.keys():
                if effect not in valid_effect_types:
                    raise ValueError(f"Unknown effect '{effect}' found in spell '{spell.name}'.")
            for validation in spell.validations.keys():
                if validation not in valid_validation_types:
                    raise ValueError(f"Unknown validation '{validation}' found in spell '{spell.name}'.")

    def get_asset_name(self, asset_id: float) -> str:
        return self.asset_id_registry.get_asset_name(asset_id)

    def _parse_numeric_dict(self, data: dict, name: str, spell_name: str) -> dict[str, float]:
        if not isinstance(data, dict): raise ValueError(f"Expected '{name}' to be a mapping in spell '{spell_name}'.")
        res = {}
        for k, v in data.items():
            if isinstance(v, str):
                res[k] = self.asset_id_registry.register_asset_name(v)
            else:
                res[k] = float(v) if not isinstance(v, bool) else (1.0 if v else 0.0)
        return res

    def _load_yaml(self, path: str) -> Dict[int, SpellDef]:
        with open(path, "r") as f:
            raw_data = yaml.safe_load(f) or {}

        # First pass: register all spell names to ensure they have IDs
        for spell_name in raw_data.keys():
            self.get_spell_id(spell_name)

        db = {}
        for spell_name, s in raw_data.items():
            if s is None: s = {}
            spell_id = self.get_spell_id(spell_name)

            triggers = s.get("triggers", {})
            if not isinstance(triggers, dict): raise ValueError(f"Expected 'triggers' to be a mapping in spell '{spell_name}'.")
            for t in triggers.keys():
                if t not in VALID_TRIGGER_TYPES: raise ValueError(f"Unknown trigger '{t}' found in spell '{spell_name}'.")

            # Convert string spell names in timeline to integer IDs
            timeline = {}
            for k, val in triggers.get(TriggerType.TIMELINE, {}).items():
                val_list = val if isinstance(val, list) else [val]
                timeline[int(k)] = [self.get_spell_id(v) for v in val_list]

            # Handle both singular and plural keys gracefully (validation/validations, effect/effects)
            raw_validations = s.get("validations", s.get("validation", {}))
            raw_effects = s.get("effects", s.get("effect", {}))

            validations = self._parse_numeric_dict(raw_validations, "validation", spell_name)
            effects = self._parse_numeric_dict(raw_effects, "effect", spell_name)

            db[spell_id] = SpellDef(
                spell_id=spell_id,
                name=spell_name,
                validations=validations,
                effects=effects,
                timeline=timeline,
            )
        return db