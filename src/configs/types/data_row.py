from dataclasses import dataclass
from src.models.components import GameObj

@dataclass(slots=True)
class DataRow:
    ## Identifiers
    data_id: int = 0
    data_name: str = ""
    cascade_seq: list[int] = []

    ## Spell data
    # Power
    spell_power_mean: float = 1.0
    spell_power_variance: float = 0.0

    # Cooldowns and cast time (in ms)
    spell_cast_build_time: int = 0
    spell_cast_channel_time: int = 0
    spell_cast_channel_ticks: int = 1
    spell_cast_cooldown: int = 0
    spell_cast_gcd_modifier: float = 1.0

    # Spell range
    spell_range_min: float = 0.0
    spell_range_max: float = 1_000_000.0

    # Spell target cap
    spell_aoe_target_cap: int = 1

    # Mana or energy cost
    spell_resource_cost: float = 0.0

    # Appearance and cosmetics
    spell_file_icon_name: str = ""
    spell_file_audio_name: str = ""
    spell_file_audio_volume: float = 1.0
    spell_file_animation_name: str = ""
    spell_file_animation_scale: float = 1.0
    spell_file_animate_on_target: bool = False

    # Spell targeting
    spell_aim_self: bool = False
    spell_aim_current_target: bool = False
    spell_aim_parent: bool = False
    spell_aim_default_friendly: bool = False
    spell_aim_default_enemy: bool = False
    spell_aim_current_targets_target: bool = False
    spell_aim_parents_current_target: bool = False
    spell_aim_next_target: bool = False

    # Spell movement
    spell_move_up: bool = False
    spell_move_left: bool = False
    spell_move_down: bool = False
    spell_move_right: bool = False
    spell_move_towards_current_target: bool = False

    ## Aura data (if spell has Aura to spawn)
    aura_effect_id: int = 0
    aura_duration_in_ms: int = 0
    aura_ticks: int = 1
    aura_max_stacks: int = 1

    ## Game object data (if spell has GameObj to spawn)
    # Position
    game_obj_pos_x_offset: float = 0.0
    game_obj_pos_y_offset: float = 0.0
    game_obj_pos_angle_offset: float = 0.0
    game_obj_stat_move_speed: float = 1.0
    game_obj_stat_hitbox_radius: float = 0.0
    game_obj_stat_has_hitbox: bool = True

    # Combat resources
    game_obj_resource_hp_current: float = 0.0
    game_obj_resource_hp_max: float = 0.0
    game_obj_is_targetable: bool = True

    # Appearance and cosmetics
    game_obj_visuals_sprite_name: str = ""
    game_obj_visuals_display_size: float = 1.0
    game_obj_visuals_color: tuple[int, int, int] = (0, 0, 0)

