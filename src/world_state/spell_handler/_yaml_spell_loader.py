import yaml
from enum import Enum
from typing import Dict

from src.settings import Consts
from .spell_def import SpellDef


class TriggerType(str, Enum):
    TIMELINE = "timeline"
    AOE_SPELL = "aoe_spell"
    SIGNAL_SPELL = "on_signal"

VALID_TRIGGER_TYPES = {t.value for t in TriggerType}

class TriggerEffect(str, Enum):
    SPAWN_AS_CHILD = "spawn_as_child"
    SEND_AS_SIGNAL = "cast_as_signal"
    FIRE_WITH_DELAY = "delay_event"

class SelfcastValidation(str, Enum):
    IS_SELFCAST = "is_selfcast"
    FULL_AOE = "full_aoe"


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
        self.spell_database: dict[int, SpellDef] = self._load_yaml(yaml_path)

    def validate_types(self, valid_effect_types: set[str], valid_validation_types: set[str]) -> None:
        """Called externally after loading to ensure all parsed keys are valid."""
        for spell_id, spell in self.spell_database.items():
            for effect in spell.effects.keys():
                if effect not in valid_effect_types:
                    raise ValueError(f"Unknown effect '{effect}' found in spell_id {spell_id}.")
            for validation in spell.validations.keys():
                if validation not in valid_validation_types:
                    raise ValueError(f"Unknown validation '{validation}' found in spell_id {spell_id}.")

    def get_asset_name(self, asset_id: float) -> str:
        return self.asset_id_registry.get_asset_name(asset_id)

    def _parse_numeric_dict(self, data: dict, name: str, spell_id: int) -> dict[str, float]:
        if not isinstance(data, dict): raise ValueError(f"Expected '{name}' to be a mapping in spell_id {spell_id}.")
        res = {}
        for k, v in data.items():
            # Validation removed from here; it now happens in validate_types()
            if isinstance(v, str):
                res[k] = self.asset_id_registry.register_asset_name(v)
            else:
                res[k] = float(v) if not isinstance(v, bool) else (1.0 if v else 0.0)
        return res

    def _load_yaml(self, path: str) -> Dict[int, SpellDef]:
        with open(path, "r") as f:
            raw_data = yaml.safe_load(f) or {}

        db = {}
        for spell_id, s in {int(k): v for k, v in raw_data.items()}.items():
            name = s.get("name")
            triggers = s.get("triggers", {})
            if not isinstance(triggers, dict): raise ValueError(f"Expected 'triggers' to be a mapping in spell_id {spell_id}.")
            for t in triggers.keys():
                if t not in VALID_TRIGGER_TYPES: raise ValueError(f"Unknown trigger '{t}' found in spell_id {spell_id}.")

            cascade = s.get("cascade", [])
            cascade = [int(c) for c in (cascade if isinstance(cascade, list) else [cascade])]

            timeline = {int(k): [int(v) for v in (val if isinstance(val, list) else [val])] for k, val in triggers.get(TriggerType.TIMELINE, {}).items()}
            signal_spell_id = int(triggers.get(TriggerType.SIGNAL_SPELL) or Consts.EMPTY_SPELL_ID)
            aoe_spell_id = int(triggers.get(TriggerType.AOE_SPELL) or Consts.EMPTY_SPELL_ID)

            # Parse blindly first
            validations = self._parse_numeric_dict(s.get("validations", {}), "validation", spell_id)
            effects = self._parse_numeric_dict(s.get("effects", {}), "effect", spell_id)

            db[spell_id] = SpellDef(
                spell_id=spell_id,
                name=name,
                validations=validations,
                effects=effects,
                timeline=timeline,
                aoe_spell_id=aoe_spell_id,
                signal_spell_id=signal_spell_id,
                cascade=cascade
            )
        return db