import yaml
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from src.settings import Consts
from .display_obj import DisplayObj
from ._casting_system import CastingEffect, CastingValidation
from ._health_system import HealthEffect, HealthValidation
from ._movement_system import MovementEffect, MovementValidation
from ._display_system import DisplayEffect, DisplayValidation
from ._attachment_system import AttachmentEffect, AttachmentValidation
from ._identity_system import IdentityEffect, IdentityValidation


class TriggerType(str, Enum):
    SPAWN_CHILD = "spawn_child"
    TIMELINE = "timeline"
    AOE_SPELL = "aoe_spell"

VALID_TRIGGER_TYPES = (
    {t.value for t in TriggerType}
)
VALID_EFFECT_TYPES = (
    {e.value for e in AttachmentEffect} |
    {e.value for e in CastingEffect} |
    {e.value for e in DisplayEffect} |
    {e.value for e in HealthEffect} |
    {e.value for e in IdentityEffect} |
    {e.value for e in MovementEffect}
)
VALID_VALIDATION_TYPES = (
    {v.value for v in AttachmentValidation} |
    {v.value for v in CastingValidation} |
    {v.value for v in DisplayValidation} |
    {v.value for v in HealthValidation} |
    {v.value for v in IdentityValidation} |
    {v.value for v in MovementValidation}
)


class RegistryForAssetIDs:
    """
    Two-way mapping between strings and float asset_ids.
    Any string encountered while loading spell data (e.g. an audio file name,
    sprite name, etc.) gets assigned a unique float asset_ids so it can flow
    through the float-only effect/validation pipeline. Later, an asset_id can
    be converted back into the original asset name to actually load the asset.
    """
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
        if int(asset_id) == Consts.EMPTY_ID:
            return ""
        result = self._asset_id_to_name.get(asset_id)
        if result is None:
            raise KeyError(f"No string registered for asset_id {asset_id}.")
        return result


@dataclass(slots=True)
class SpellDef:
    spell_id: int
    name: str = ""
    validations: dict[str, float] = field(default_factory=dict)
    effects: dict[str, float] = field(default_factory=dict)
    spawn_child: list[int] = field(default_factory=list)
    timeline: dict[int, list[int]] = field(default_factory=dict)
    aoe_spell_id: int = Consts.EMPTY_ID


class YamlSpellLoader:
    def __init__(self, yaml_path: str = "data/spells.yaml") -> None:
        self.asset_id_registry = RegistryForAssetIDs()
        self.spell_database: dict[int, SpellDef] = self._load_yaml(yaml_path)

    def fetch_asset_names_for_display_obj(self, display_obj: DisplayObj) -> DisplayObj:
        display_obj.sprite_name = self.asset_id_registry.get_asset_name(display_obj.sprite_id)
        display_obj.audio_name = self.asset_id_registry.get_asset_name(display_obj.audio_id)
        return display_obj

    def get_asset_name(self, asset_id: float) -> str:
        return self.asset_id_registry.get_asset_name(asset_id)

    def _parse_numeric_dict(self, data: dict, valid_keys: set, name: str, spell_id: int) -> dict[str, float]:
        if not isinstance(data, dict): raise ValueError(f"Expected '{name}' to be a mapping in spell_id {spell_id}.")
        res = {}
        for k, v in data.items():
            if k not in valid_keys: raise ValueError(f"Unknown {name} '{k}' found in spell_id {spell_id}.")
            if isinstance(v, str):
                res[k] = self.asset_id_registry.register_asset_name(v)
            else:
                res[k] = float(v) if not isinstance(v, bool) else (1.0 if v else 0.0)
        return res

    def _parse_string_dict(self, data: dict, valid_keys: set, name: str, spell_id: int) -> dict[str, str]:
        if not isinstance(data, dict): raise ValueError(f"Expected '{name}' to be a mapping in spell_id {spell_id}.")
        res = {}
        for k, v in data.items():
            if k not in valid_keys: raise ValueError(f"Unknown {name} '{k}' found in spell_id {spell_id}.")
            res[k] = str(v)
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

            spawn_child = triggers.get(TriggerType.SPAWN_CHILD, [])
            spawn_child = [int(c) for c in (spawn_child if isinstance(spawn_child, list) else [spawn_child])]

            timeline = {int(k): [int(v) for v in (val if isinstance(val, list) else [val])] for k, val in triggers.get(TriggerType.TIMELINE, {}).items()}

            aoe_spell_id = triggers.get(TriggerType.AOE_SPELL)
            if aoe_spell_id is None:
                aoe_spell_id = Consts.EMPTY_ID
            else:
                aoe_spell_id = int(aoe_spell_id)

            validations = self._parse_numeric_dict(s.get("validations", {}), VALID_VALIDATION_TYPES, "validation", spell_id)
            effects = self._parse_numeric_dict(s.get("effects", {}), VALID_EFFECT_TYPES, "effect", spell_id)

            # Sanity Checks
            if CastingEffect.APPLY_COOLDOWN in effects: assert CastingValidation.IS_COOLDOWN_READY in validations, f"Spell {spell_id} missing cooldown validation."
            if CastingEffect.APPLY_GCD in effects: assert CastingValidation.IS_GCD_READY in validations, f"Spell {spell_id} missing gcd validation."
            if CastingEffect.APPLY_TICKS_SUBTRACTION in effects and effects[CastingEffect.APPLY_TICKS_SUBTRACTION] != 65535:
                assert CastingValidation.ARE_TICKS_READY in validations, f"Spell {spell_id} missing tick validation."
                assert validations[CastingValidation.ARE_TICKS_READY] == effects[CastingEffect.APPLY_TICKS_SUBTRACTION], f"Spell {spell_id} tick validation/effect mismatch."
            if "range_limit" in effects:
                assert MovementValidation.IS_WITHIN_RANGE_OF_DESTINATION in validations, f"Spell {spell_id} missing range validation."
                assert validations[MovementValidation.IS_WITHIN_RANGE_OF_DESTINATION] == effects["range_limit"], f"Spell {spell_id} range validation/effect mismatch."

            db[spell_id] = SpellDef(
                spell_id=spell_id,
                name=name,
                validations=validations,
                effects=effects,
                spawn_child=spawn_child,
                timeline=timeline,
                aoe_spell_id=aoe_spell_id,
            )
        return db