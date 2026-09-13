import yaml
from dataclasses import dataclass, field
from typing import Dict

VALID_EFFECT_TYPES = {
    "damage",
    "heal",
    "walk_forward",
    "stop_walk_forward",
    "walk_backward",
    "stop_walk_backward",
    "walk_left",
    "stop_walk_left",
    "walk_right",
    "stop_walk_right",
    "walk_towards_target",
    "stop_walk_towards_target",
    "teleport_to_target",
    "push_target",
    "update_current_target",
    "targetswap_to_other_team",
    "targetswap_to_parent",
    "teamswap",
    "despawn_self",
    "add_channeling_ticks",
    "consume_channeling_ticks",
    "hp",
    "x_offset",
    "y_offset",
    "movespeed",
    "is_enemy",
    "is_boss",
    "is_player",
    "color_red",
    "color_green",
    "color_blue",
    "base_cooldown",
    "gcd_mod",
    "range_limit",
}

VALID_VALIDATION_TYPES = {
    "is_within_range",
    "source_is_valid",
    "is_cooldown_ready",
    "is_gcd_ready",
    "has_channeling_ticks",
}

VALID_TRIGGER_TYPES = {
    "spawn_child",
    "timeline",
    "aoe_cross_team",
    "aoe_same_team",
}

VALID_COSMETIC_TYPES = {
    "audio_name",
    "animation_name",
    "sprite_name",
}

@dataclass(slots=True)
class SpellDef:
    spell_id: int
    name: str

    # Runtime Validations, Effects & Cosmetics
    validations: dict[str, float] = field(default_factory=dict)
    effects: dict[str, float] = field(default_factory=dict)
    cosmetics: dict[str, str] = field(default_factory=dict)
    # Cosmetic Properties
    animation_scale: float = 1.0

    # Triggers (Parsed from 'triggers' key)
    spawn_child: list[int] = field(default_factory=list)
    timeline: dict[int, list[int]] = field(default_factory=dict)
    flag_aoe_cross_team: bool = False
    flag_aoe_same_team: bool = False

class SpellLoader:
    def __init__(self, yaml_path: str = "data/spells.yaml") -> None:
        self.spell_database: Dict[int, SpellDef] = self._load_yaml(yaml_path)

    def _load_yaml(self, path: str) -> Dict[int, SpellDef]:
        with open(path, "r") as f:
            raw_data = yaml.safe_load(f) or {}

        # Ensure keys are correctly typed as integers.
        raw_data = {int(k): v for k, v in raw_data.items()}

        db = {}
        for spell_id, s in raw_data.items():
            # --------------------------------------------------
            # Parse Triggers
            # --------------------------------------------------
            trigger_data = s.get("triggers", {})
            if not isinstance(trigger_data, dict):
                raise ValueError(f"Expected 'triggers' to be a mapping in spell_id {spell_id}.")

            for raw_type in trigger_data.keys():
                if raw_type not in VALID_TRIGGER_TYPES:
                    raise ValueError(f"Unknown trigger_type '{raw_type}' found in spell_id {spell_id}.")

            spawn_child_raw = trigger_data.get("spawn_child", [])
            if not isinstance(spawn_child_raw, list):
                spawn_child_raw = [spawn_child_raw]
            spawn_child = [int(c) for c in spawn_child_raw]

            raw_timeline = trigger_data.get("timeline", {})
            timeline = {}
            for t_key, t_val in raw_timeline.items():
                if not isinstance(t_val, list):
                    t_val = [t_val]
                timeline[int(t_key)] = [int(v) for v in t_val]

            flag_aoe_cross_team = bool(trigger_data.get("aoe_cross_team", False))
            flag_aoe_same_team = bool(trigger_data.get("aoe_same_team", False))

            # --------------------------------------------------
            # Parse Validations
            # --------------------------------------------------
            parsed_validations: dict[str, float] = {}
            validation_data = s.get("validations", {})

            if not isinstance(validation_data, dict):
                raise ValueError(f"Expected 'validations' to be a mapping in spell_id {spell_id}.")

            for raw_type, raw_value in validation_data.items():
                if raw_type not in VALID_VALIDATION_TYPES:
                    raise ValueError(f"Unknown validation_type '{raw_type}' found in spell_id {spell_id}.")

                if isinstance(raw_value, bool):
                    parsed_validations[raw_type] = 1.0 if raw_value else 0.0
                elif isinstance(raw_value, (int, float)):
                    parsed_validations[raw_type] = float(raw_value)
                else:
                    raise ValueError(
                        f"Expected boolean or numeric value for validation '{raw_type}' "
                        f"in spell_id {spell_id}, got {type(raw_value).__name__}."
                    )

            # --------------------------------------------------
            # Parse Effects
            # --------------------------------------------------
            parsed_effects: dict[str, float] = {}
            effect_data = s.get("effects", {})

            if not isinstance(effect_data, dict):
                raise ValueError(f"Expected 'effects' to be a mapping in spell_id {spell_id}.")

            for raw_type, raw_value in effect_data.items():
                if raw_type not in VALID_EFFECT_TYPES:
                    raise ValueError(f"Unknown effect_type '{raw_type}' found in spell_id {spell_id}.")

                if isinstance(raw_value, bool):
                    parsed_effects[raw_type] = 1.0 if raw_value else 0.0
                elif isinstance(raw_value, (int, float)):
                    parsed_effects[raw_type] = float(raw_value)
                else:
                    raise ValueError(
                        f"Expected boolean or numeric value for effect '{raw_type}' "
                        f"in spell_id {spell_id}, got {type(raw_value).__name__}."
                    )

            # --------------------------------------------------
            # Parse Cosmetics
            # --------------------------------------------------
            parsed_cosmetics: dict[str, str] = {}
            cosmetic_data = s.get("cosmetics", {})

            if not isinstance(cosmetic_data, dict):
                raise ValueError(f"Expected 'cosmetics' to be a mapping in spell_id {spell_id}.")

            for raw_type, raw_value in cosmetic_data.items():
                if raw_type not in VALID_COSMETIC_TYPES:
                    raise ValueError(f"Unknown cosmetic_type '{raw_type}' found in spell_id {spell_id}.")
                parsed_cosmetics[raw_type] = str(raw_value)

            # --------------------------------------------------
            # Sanity Checks (Assertions)
            # --------------------------------------------------
            if "base_cooldown" in parsed_effects:
                assert "is_cooldown_ready" in parsed_validations, f"Spell {spell_id} has 'base_cooldown' effect but is missing 'is_cooldown_ready' validation."

            if "gcd_mod" in parsed_effects:
                assert "is_gcd_ready" in parsed_validations, f"Spell {spell_id} has 'gcd_mod' effect but is missing 'is_gcd_ready' validation."

            if "consume_channeling_ticks" in parsed_effects:
                assert "has_channeling_ticks" in parsed_validations, f"Spell {spell_id} has 'consume_channeling_ticks' effect but is missing 'has_channeling_ticks' validation."
                assert parsed_validations["has_channeling_ticks"] == parsed_effects["consume_channeling_ticks"], f"Spell {spell_id} 'has_channeling_ticks' validation value must match 'consume_channeling_ticks' effect value."

            if "range_limit" in parsed_effects:
                assert "is_within_range" in parsed_validations, f"Spell {spell_id} has 'range_limit' effect but is missing 'is_within_range' validation."
                assert parsed_validations["is_within_range"] == parsed_effects["range_limit"], f"Spell {spell_id} 'is_within_range' validation value must match 'range_limit' effect value."

            # --------------------------------------------------
            # Create Spell Definition
            # --------------------------------------------------
            db[spell_id] = SpellDef(
                spell_id=spell_id,
                name=s.get("name", ""),
                animation_scale=float(s.get("animation_scale", 1.0)),
                validations=parsed_validations,
                effects=parsed_effects,
                cosmetics=parsed_cosmetics,
                spawn_child=spawn_child,
                timeline=timeline,
                flag_aoe_cross_team=flag_aoe_cross_team,
                flag_aoe_same_team=flag_aoe_same_team,
            )

        return db