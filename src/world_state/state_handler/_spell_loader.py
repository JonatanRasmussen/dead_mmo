import yaml
from pathlib import Path
from typing import Optional

# Assuming these imports match your project structure:
from src.settings import HardwareInputConsts
from .temp_registry import AssetRegistry

from ._casting_system import CastingSystem, SpellCastingData, CastingBehavior
from ._health_system import HealthSystem, SpellHealthData, HealthBehavior
from ._movement_system import MovementSystem, SpellMovementData, MovementBehavior
from ._targeting_system import TargetingSystem, SpellTargetingData, TargetingBehavior
from ._vfx_and_sfx_system import VfxAndSfxSystem, SpellVfxData, SpellVisualTemplate


class SpellLoader:
    # Set this to True when you are ready to drop hardcoded Integer IDs entirely.
    # (Requires updating the YAML file keys/timelines to strings first).
    USE_AUTO_IDS = False

    def __init__(self, yaml_path: str = "data/spells.yaml") -> None:
        self._raw_spells: dict[int, dict] = self._load_yaml(yaml_path)

    def _load_yaml(self, path: str) -> dict[int, dict]:
        with open(path, "r") as f:
            raw_data = yaml.safe_load(f) or {}

        if self.USE_AUTO_IDS:
            return self._apply_auto_ids(raw_data)

        # Ensure keys are correctly typed as integers for now.
        return {int(k): v for k, v in raw_data.items()}

    def _apply_auto_ids(self, raw_data: dict) -> dict[int, dict]:
        """
        Dynamically generates incrementing IDs based on alphabetical sort of spell names.
        Automatically maps string IDs in timelines and hardware bindings into integers.
        """
        name_to_id = {name: i + 1 for i, name in enumerate(sorted(raw_data.keys()))}
        new_data = {}

        for name, spell in raw_data.items():
            assigned_id = name_to_id[name]
            spell["spell_id"] = assigned_id

            # 1. Update timeline references
            if "timeline" in spell:
                new_timeline = {}
                for ms_tick, spell_list in spell["timeline"].items():
                    new_timeline[ms_tick] = [name_to_id[s] for s in spell_list]
                spell["timeline"] = new_timeline

            # 2. Update timeline generators
            gen = spell.get("timeline_generator")
            if gen and "spell_id" in gen:
                gen["spell_id"] = name_to_id[gen["spell_id"]]

            # 3. Update hardware bindings
            if "hardware_bindings" in spell:
                new_bindings = {}
                for bind, target_spell in spell["hardware_bindings"].items():
                    new_bindings[bind] = name_to_id[target_spell]
                spell["hardware_bindings"] = new_bindings

            new_data[assigned_id] = spell
        return new_data

    # --- System Factories ---

    def create_casting_system(self) -> CastingSystem:
        data_dct = {}
        for spell_id, s in self._raw_spells.items():
            flags = CastingBehavior.NONE
            if s.get("deny_if_casting"): flags |= CastingBehavior.DENY_IF_CASTING
            if s.get("start_channel"): flags |= CastingBehavior.START_CHANNEL
            if s.get("stop_channel"): flags |= CastingBehavior.STOP_CHANNEL

            timeline = s.get("timeline", {})
            gen = s.get("timeline_generator")
            if gen and gen.get("type") == "channel":
                interval = gen["duration"] // gen["ticks"]
                timeline = {interval * i: [gen["spell_id"]] for i in range(1, gen["ticks"] + 1)}

            # Map hardware bindings strings to actual Constants
            bindings = {}
            for key_str, target_id in s.get("hardware_bindings", {}).items():
                actual_key = getattr(HardwareInputConsts, key_str, None)
                if actual_key is not None:
                    bindings[actual_key] = target_id

            data_dct[spell_id] = SpellCastingData(
                flags=flags,
                timeline=timeline,
                base_cooldown=s.get("base_cooldown", 0),
                gcd_mod=s.get("gcd_mod", 0.0),
                hardware_bindings=bindings
            )
        return CastingSystem(data_dct)

    def create_health_system(self) -> HealthSystem:
        data_dct = {}
        for spell_id, s in self._raw_spells.items():
            flags = HealthBehavior.NONE
            if s.get("damaging"): flags |= HealthBehavior.DAMAGING
            if s.get("healing"): flags |= HealthBehavior.HEALING

            data_dct[spell_id] = SpellHealthData(
                power=s.get("power", 1.0),
                flags=flags,
                hp=s.get("hp", 0.0)
            )
        return HealthSystem(data_dct)

    def create_movement_system(self) -> MovementSystem:
        data_dct = {}
        for spell_id, s in self._raw_spells.items():
            # Enums are mutually exclusive, so we pick the first match
            behavior = MovementBehavior.NONE
            if s.get("walk_forward"): behavior = MovementBehavior.WALK_FORWARD
            elif s.get("walk_left"): behavior = MovementBehavior.WALK_LEFT
            elif s.get("walk_backward"): behavior = MovementBehavior.WALK_BACKWARD
            elif s.get("walk_right"): behavior = MovementBehavior.WALK_RIGHT
            elif s.get("stop_walk_forward"): behavior = MovementBehavior.STOP_WALK_FORWARD
            elif s.get("stop_walk_left"): behavior = MovementBehavior.STOP_WALK_LEFT
            elif s.get("stop_walk_backward"): behavior = MovementBehavior.STOP_WALK_BACKWARD
            elif s.get("stop_walk_right"): behavior = MovementBehavior.STOP_WALK_RIGHT
            elif s.get("walk_source_towards_target"): behavior = MovementBehavior.WALK_SOURCE_TOWARDS_TARGET
            elif s.get("stop_walk_source_towards_target"): behavior = MovementBehavior.STOP_WALK_SOURCE_TOWARDS_TARGET
            elif s.get("teleport_source_to_target"): behavior = MovementBehavior.TELEPORT_SOURCE_TO_TARGET
            elif s.get("despawn_self"): behavior = MovementBehavior.DESPAWN_SELF
            elif s.get("push_target_away_from_source"): behavior = MovementBehavior.PUSH_TARGET_AWAY_FROM_SOURCE

            data_dct[spell_id] = SpellMovementData(
                movement_force=s.get("movement_force", 1.0),
                range_limit=s.get("range_limit", 0.0),
                behavior=behavior,
                spawned_x_offset=s.get("spawned_x_offset", 0.0),
                spawned_y_offset=s.get("spawned_y_offset", 0.0),
                spawned_movespeed=s.get("spawned_movespeed", 1.0)
            )
        return MovementSystem(data_dct)

    def create_targeting_system(self) -> TargetingSystem:
        data_dct = {}
        for spell_id, s in self._raw_spells.items():
            flags = TargetingBehavior.NONE
            if s.get("aoe_cross_team"): flags |= TargetingBehavior.AOE_CROSS_TEAM
            if s.get("aoe_same_team"): flags |= TargetingBehavior.AOE_SAME_TEAM
            if s.get("spawn_boss"): flags |= TargetingBehavior.SPAWN_BOSS
            if s.get("spawn_player"): flags |= TargetingBehavior.SPAWN_PLAYER
            if s.get("spawn_obj"): flags |= TargetingBehavior.SPAWN_OBJ
            if s.get("despawn_self"): flags |= TargetingBehavior.DESPAWN_SELF
            if s.get("update_current_target"): flags |= TargetingBehavior.UPDATE_CURRENT_TARGET
            if s.get("targetswap_to_other_team"): flags |= TargetingBehavior.TARGETSWAP_TO_OTHER_TEAM
            if s.get("targetswap_to_parent"): flags |= TargetingBehavior.TARGETSWAP_TO_PARENT
            if s.get("teamswap"): flags |= TargetingBehavior.TEAMSWAP

            data_dct[spell_id] = SpellTargetingData(
                spell_id=spell_id,
                is_enemy=s.get("spawn_boss", False),
                is_boss_or_player=(s.get("spawn_boss", False) or s.get("spawn_player", False)),
                flags=flags
            )
        return TargetingSystem(data_dct)

    def create_vfx_and_sfx_system(self) -> VfxAndSfxSystem:
        data_dct = {}
        for spell_id, s in self._raw_spells.items():
            spawn_template = None
            spawn_template = SpellVisualTemplate(
                color_red=s.get("spawn_color_red", 128),
                color_green=s.get("spawn_color_green", 128),
                color_blue=s.get("spawn_color_blue", 128),
                sprite_name=s.get("spawn_sprite_name") or AssetRegistry.get_sprite(spell_id),
                audio_name=s.get("spawn_audio_name", "")
            )

            data_dct[spell_id] = SpellVfxData(
                audio_name=s.get("audio_name") or AssetRegistry.get_audio(spell_id),
                animation_name=s.get("animation_name", ""),
                animation_scale=s.get("animation_scale", 1.0),
                animate_on_source=s.get("animate_on_source", False),
                animate_on_target=s.get("animate_on_target", False),
                spawn_template=spawn_template
            )
        return VfxAndSfxSystem(data_dct)