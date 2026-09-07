import yaml
from dataclasses import dataclass, field
from typing import Dict
from src.settings import HardwareInputConsts

VALID_EFFECT_TYPES = {
    "damage", "heal", "walk_forward", "stop_walk_forward", "walk_backward",
    "stop_walk_backward", "walk_left", "stop_walk_left", "walk_right",
    "stop_walk_right", "walk_towards_target", "stop_walk_towards_target",
    "teleport_to_target", "push_target", "update_current_target",
    "targetswap_to_other_team", "targetswap_to_parent", "teamswap",
    "despawn_self", "start_channel", "stop_channel", "spawn_obj"
}

@dataclass(slots=True)
class Effect:
    effect_type: str  # Replaced Enum with str
    amount: float = 0.0
    force: float = 0.0
    hp: float = 0.0
    x_offset: float = 0.0
    y_offset: float = 0.0
    movespeed: float = 1.0
    is_enemy: bool = False
    is_boss: bool = False
    is_player: bool = False
    color_red: int = 255
    color_green: int = 255
    color_blue: int = 255
    sprite_name: str = ""

@dataclass(slots=True)
class SpellDef:
    spell_id: int
    name: str

    # Base Spell Properties
    base_cooldown: int = 0
    gcd_mod: float = 0.0
    timeline: dict[int, list[int]] = field(default_factory=dict)
    hardware_bindings: dict[str, int] = field(default_factory=dict)

    # Targeting Properties
    flag_aoe_cross_team: bool = False
    flag_aoe_same_team: bool = False
    range_limit: float = 0.0

    # Visual Properties
    audio_name: str = ""
    animation_name: str = ""
    animation_scale: float = 1.0

    # The flat Effect List
    effects: list[Effect] = field(default_factory=list)

class SpellLoader:
    def __init__(self, yaml_path: str = "data/spells.yaml") -> None:
        self.spell_database: Dict[int, SpellDef] = self._load_yaml(yaml_path)

    def _load_yaml(self, path: str) -> Dict[int, SpellDef]:
        with open(path, "r") as f:
            raw_data = yaml.safe_load(f) or {}

        # Ensure keys are correctly typed as integers for now.
        raw_data = {int(k): v for k, v in raw_data.items()}

        db = {}

        for spell_id, s in raw_data.items():
            # Parse Timelines
            timeline = s.get("timeline", {})
            gen = s.get("timeline_generator")
            if gen and gen.get("type") == "channel":
                interval = gen["duration"] // gen["ticks"]
                timeline = {interval * i: [gen["spell_id"]] for i in range(1, gen["ticks"] + 1)}

            # Parse Hardware Bindings
            bindings = {}
            for key_str, target_id in s.get("hardware_bindings", {}).items():
                actual_key = getattr(HardwareInputConsts, key_str, None)
                if actual_key is not None:
                    bindings[actual_key] = target_id

            # Parse Effects
            parsed_effects = []
            for effect_data in s.get("effects", []):
                raw_type = effect_data.get("type", "")

                # Assertion checking that the yaml effect string exists in the valid types
                assert raw_type in VALID_EFFECT_TYPES, f"ValueError: Unknown effect_type '{raw_type}' found in spell_id {spell_id}."

                parsed_effects.append(Effect(
                    effect_type=raw_type,
                    amount=float(effect_data.get("amount", 0.0)),
                    force=float(effect_data.get("force", 0.0)),
                    hp=float(effect_data.get("hp", 0.0)),
                    x_offset=float(effect_data.get("x_offset", 0.0)),
                    y_offset=float(effect_data.get("y_offset", 0.0)),
                    movespeed=float(effect_data.get("movespeed", 1.0)),
                    is_enemy=effect_data.get("is_enemy", False),
                    is_boss=effect_data.get("is_boss", False),
                    is_player=effect_data.get("is_player", False),
                    color_red=int(effect_data.get("color_red", 255)),
                    color_green=int(effect_data.get("color_green", 255)),
                    color_blue=int(effect_data.get("color_blue", 255)),
                    sprite_name=effect_data.get("sprite_name", "")
                ))

            db[spell_id] = SpellDef(
                spell_id=spell_id,
                name=s.get("name", ""),
                base_cooldown=s.get("base_cooldown", 0),
                gcd_mod=s.get("gcd_mod", 0.0),
                timeline=timeline,
                hardware_bindings=bindings,
                flag_aoe_cross_team=s.get("aoe_cross_team", False),
                flag_aoe_same_team=s.get("aoe_same_team", False),
                range_limit=float(s.get("range_limit", 0.0)),
                audio_name=s.get("audio_name", ""),
                animation_name=s.get("animation_name", ""),
                animation_scale=float(s.get("animation_scale", 1.0)),
                effects=parsed_effects
            )
        return db