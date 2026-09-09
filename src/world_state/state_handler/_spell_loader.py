import yaml
from dataclasses import dataclass, field
from typing import Dict
from src.settings import Consts

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

    # Child Spawns
    spawn_child: list[int] = field(default_factory=list)

    # Base Spell Properties
    base_cooldown: int = 0
    gcd_mod: float = 0.0
    timeline: dict[int, list[int]] = field(default_factory=dict)

    # Targeting Properties
    flag_aoe_cross_team: bool = False
    flag_aoe_same_team: bool = False
    range_limit: float = 0.0

    # Visual Properties
    animation_scale: float = 1.0

    # Runtime Effects
    effects: dict[str, float] = field(default_factory=dict)
    cosmetics: dict[str, str] = field(default_factory=dict)

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
            # Parse Spawn Child
            # --------------------------------------------------
            spawn_child_raw = s.get("spawn_child", [])
            if not isinstance(spawn_child_raw, list):
                spawn_child_raw = [spawn_child_raw]
            spawn_child = [int(c) for c in spawn_child_raw]

            # --------------------------------------------------
            # Parse Timelines
            # --------------------------------------------------
            timeline = s.get("timeline", {})

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
            # Create Spell Definition
            # --------------------------------------------------
            db[spell_id] = SpellDef(
                spell_id=spell_id,
                name=s.get("name", ""),
                spawn_child=spawn_child,
                base_cooldown=s.get("base_cooldown", 0),
                gcd_mod=s.get("gcd_mod", 0.0),
                timeline=timeline,
                flag_aoe_cross_team=s.get("aoe_cross_team", False),
                flag_aoe_same_team=s.get("aoe_same_team", False),
                range_limit=float(s.get("range_limit", 0.0)),
                animation_scale=float(s.get("animation_scale", 1.0)),
                effects=parsed_effects,
                cosmetics=parsed_cosmetics,
            )

        return db