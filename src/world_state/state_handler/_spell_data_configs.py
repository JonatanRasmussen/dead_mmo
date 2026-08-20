from src.settings import AudioFiles, Colors, Consts, SpriteFiles, HardwareInputConsts
from ._spell_data import (
    SpellData,
    CastingSpellFlags,
    HealthSpellFlags,
    MovementSpellFlags,
    TargetingSpellFlags,
    TargetingSpellMode
)

class LegacySpellConfig:
    """A completely flattened, explicit list of all spells in the game."""

    @staticmethod
    def _channel(spell_id: int, duration: int, ticks: int) -> dict[int, list[int]]:
        """Helper to generate a timeline for channel/tick-based spells."""
        interval = duration // ticks
        return {interval * i: [spell_id] for i in range(1, ticks + 1)}

    @staticmethod
    def get_all_spells() -> list[SpellData]:
        return [
            # ==========================================
            # Basic Movement
            # ==========================================
            SpellData(
                spell_id=Consts.EMPTY_ID,
                name="empty_spell",
            ),
            SpellData(
                spell_id=91,
                name="start_move_up",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.MOVE_UP
            ),
            SpellData(
                spell_id=92,
                name="stop_move_up",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.STOP_MOVE_UP
            ),
            SpellData(
                spell_id=181,
                name="start_move_left",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.MOVE_LEFT
            ),
            SpellData(
                spell_id=182,
                name="stop_move_left",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.STOP_MOVE_LEFT
            ),
            SpellData(
                spell_id=271,
                name="start_move_down",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.MOVE_DOWN
            ),
            SpellData(
                spell_id=272,
                name="stop_move_down",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.STOP_MOVE_DOWN
            ),
            SpellData(
                spell_id=1,
                name="start_move_right",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.MOVE_RIGHT
            ),
            SpellData(
                spell_id=2,
                name="stop_move_right",
                targeting=TargetingSpellMode.SELF,
                movement_behavior=MovementSpellFlags.STOP_MOVE_RIGHT
            ),
            SpellData(
                spell_id=361,
                name="step_towards_target",
                targeting=TargetingSpellMode.TARGET,
                movement_behavior=MovementSpellFlags.MOVE_TOWARDS_TARGET
            ),
            SpellData(
                spell_id=362,
                name="start_move_towards_target",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.START_CHANNEL,
                movement_behavior=MovementSpellFlags.MOVE_TOWARDS_TARGET,
                timeline=LegacySpellConfig._channel(361, 60000, 60 * Consts.MOVEMENT_UPDATES_PER_SECOND)
            ),
            SpellData(
                spell_id=363,
                name="stop_move_towards_target",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.STOP_CHANNEL,
                movement_behavior=MovementSpellFlags.STOP_MOVE_TOWARDS_TARGET
            ),

            # ==========================================
            # Basic Targeting
            # ==========================================
            SpellData(
                spell_id=15,
                name="targetswap_to_next_tab_target",
                targeting=TargetingSpellMode.TAB_TO_NEXT,
                targeting_behavior=TargetingSpellFlags.UPDATE_CURRENT_TARGET
            ),
            SpellData(
                spell_id=16,
                name="targetswap_to_parent",
                targeting=TargetingSpellMode.PARENT,
                targeting_behavior=TargetingSpellFlags.UPDATE_CURRENT_TARGET
            ),

            # ==========================================
            # Npc Healing Powerup
            # ==========================================
            SpellData(
                spell_id=214,
                name="healing_burst_tick",
                targeting=TargetingSpellMode.TARGET,
                movement_behavior=MovementSpellFlags.DESPAWN_SELF,
                health_behavior=HealthSpellFlags.HEALING,
                targeting_behavior=TargetingSpellFlags.DESPAWN_SELF,
                power=150.0,
                range_limit=0.1
            ),
            SpellData(
                spell_id=215,
                name="healing_burst_apply",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.START_CHANNEL,
                timeline=LegacySpellConfig._channel(214, 15000, 150)
            ),
            SpellData(
                spell_id=171,
                name="spawn_healing_powerup",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.TRIGGER_GCD,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ,
                timeline={100: [16], 200: [215]},
                hp=30.0,
                spawned_x_offset=0.2,
                spawned_y_offset=-0.2,
                audio_name=AudioFiles.REJUVENATION_APPLY,
                spawn_color=Colors.GREEN
            ),

            # ==========================================
            # Npc Landmine
            # ==========================================
            SpellData(
                spell_id=114,
                name="landmine_explosion_tick",
                targeting=TargetingSpellMode.DEFAULT_CROSS_TEAM,
                movement_behavior=MovementSpellFlags.DESPAWN_SELF,
                health_behavior=HealthSpellFlags.DAMAGING,
                targeting_behavior=TargetingSpellFlags.DESPAWN_SELF,
                power=150.0,
                range_limit=0.1
            ),
            SpellData(
                spell_id=115,
                name="landmine_explosion_apply",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.START_CHANNEL,
                timeline=LegacySpellConfig._channel(114, 15000, 150)
            ),
            SpellData(
                spell_id=71,
                name="spawn_landmine",
                targeting=TargetingSpellMode.SELF,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ,
                timeline={1500: [115]},
                hp=20.0,
                spawned_x_offset=-0.5,
                spawned_y_offset=0.1,
                spawn_color=Colors.MAGENTA
            ),

            # ==========================================
            # Npc Target Dummy
            # ==========================================
            SpellData(
                spell_id=70,
                name="spawn_target_dummy",
                targeting=TargetingSpellMode.SELF,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ | TargetingSpellFlags.SPAWN_BOSS,
                timeline={1500: [15], 4000: [128], 7000: [362]},
                hp=80.0,
                spawned_x_offset=-0.2,
                spawned_y_offset=0.1,
                spawn_color=Colors.BLUE
            ),
            SpellData(
                spell_id=970,
                name="spawn_bravo_dummy",
                targeting=TargetingSpellMode.SELF,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ | TargetingSpellFlags.SPAWN_BOSS,
                timeline={1500: [15], 2000: [941], 4000: [124], 7000: [362]},
                hp=80.0,
                spawned_x_offset=-0.2,
                spawned_y_offset=0.1,
                spawn_color=Colors.BLUE
            ),

            # ==========================================
            # Spec Warlock
            # ==========================================
            SpellData(
                spell_id=128,
                name="fire_blast",
                targeting=TargetingSpellMode.TARGET,
                casting_behavior=CastingSpellFlags.TRIGGER_GCD,
                targeting_behavior=TargetingSpellFlags.AOE,
                timeline={0: [111]}
            ),
            SpellData(
                spell_id=111,
                name="fire_blast_damage",
                targeting=TargetingSpellMode.USE_EVENT_TARGET,
                health_behavior=HealthSpellFlags.DAMAGING,
                power=13.0,
                audio_name=AudioFiles.SHADOW_BOLT_HIT
            ),
            SpellData(
                spell_id=911,
                name="shadow_blast",
                targeting=TargetingSpellMode.TARGET,
                health_behavior=HealthSpellFlags.DAMAGING,
                power=53.0,
                audio_name=AudioFiles.SHADOW_BOLT_BUILD
            ),
            SpellData(
                spell_id=112,
                name="fire_channel_tick",
                targeting=TargetingSpellMode.DEFAULT_CROSS_TEAM,
                health_behavior=HealthSpellFlags.DAMAGING,
                power=5.0,
                range_limit=0.2
            ),
            SpellData(
                spell_id=113,
                name="fire_channel_apply",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.START_CHANNEL,
                timeline=LegacySpellConfig._channel(112, 3000, 30)
            ),
            SpellData(
                spell_id=131,
                name="channel_shadowbolt",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.START_CHANNEL,
                timeline=LegacySpellConfig._channel(132, 60000, 60 * Consts.MOVEMENT_UPDATES_PER_SECOND)
            ),
            SpellData(
                spell_id=132,
                name="shadowbolt_tick",
                targeting=TargetingSpellMode.SELF,
                timeline={0: [133, 116]}
            ),
            SpellData(
                spell_id=116,
                name="shadowbolt_damage_tick",
                targeting=TargetingSpellMode.TARGET,
                movement_behavior=MovementSpellFlags.DESPAWN_SELF,
                health_behavior=HealthSpellFlags.DAMAGING,
                targeting_behavior=TargetingSpellFlags.DESPAWN_SELF,
                power=34.0,
                range_limit=0.05,
                audio_name=AudioFiles.SHADOW_BOLT_HIT
            ),
            SpellData(
                spell_id=133,
                name="shadowbolt_movement_tick",
                targeting=TargetingSpellMode.TARGET,
                movement_behavior=MovementSpellFlags.MOVE_TOWARDS_TARGET
            ),
            SpellData(
                spell_id=124,
                name="shadowbolt_spawn",
                targeting=TargetingSpellMode.TARGET,
                casting_behavior=CastingSpellFlags.TRIGGER_GCD,
                targeting_behavior=TargetingSpellFlags.AOE,
                timeline={0: [41]}
            ),
            SpellData(
                spell_id=41,
                name="shadowbolt_spawn_projectile",
                targeting=TargetingSpellMode.USE_EVENT_TARGET,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ,
                timeline={0: [131]},
                spawned_x_offset=0.0,
                spawned_y_offset=0.05,
                spawned_movespeed=5.0,
                audio_name=AudioFiles.SHADOW_BOLT_CAST,
                spawn_color=Colors.WHITE
            ),
            SpellData(
                spell_id=941,
                name="bravo_channel_shadowtick",
                targeting=TargetingSpellMode.SELF,
                casting_behavior=CastingSpellFlags.START_CHANNEL,
                timeline=LegacySpellConfig._channel(911, 1220, 4)
            ),
            SpellData(
                spell_id=42,
                name="spawn_player",
                targeting=TargetingSpellMode.SELF,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ | TargetingSpellFlags.SPAWN_PLAYER,
                hardware_bindings={
                    HardwareInputConsts.KEYBOARD_KEYDOWN_1: 128,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_2: 113,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_3: 171,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_4: 124,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: 15,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: 91,
                    HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: 92,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: 181,
                    HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: 182,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: 271,
                    HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: 272,
                    HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: 1,
                    HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: 2,
                },
                hp=30.0,
                spawned_x_offset=0.3,
                spawned_y_offset=0.3,
                spawn_color=Colors.RED,
                spawn_sprite_name=SpriteFiles.PORO_PLAYER
            ),

            # ==========================================
            # Npc Boss
            # ==========================================
            SpellData(
                spell_id=69,
                name="spawn_boss",
                targeting=TargetingSpellMode.SELF,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ | TargetingSpellFlags.SPAWN_BOSS,
                timeline={400: [70], 800: [71], 1000: [15], 3000: [128], 5000: [113]},
                hp=30.0,
                spawned_x_offset=0.7,
                spawned_y_offset=0.7,
                spawn_color=Colors.GREEN
            ),
            SpellData(
                spell_id=969,
                name="spawn_bravo_boss",
                targeting=TargetingSpellMode.SELF,
                targeting_behavior=TargetingSpellFlags.SPAWN_OBJ | TargetingSpellFlags.SPAWN_BOSS,
                timeline={400: [970], 800: [71], 1000: [15], 3000: [128], 5000: [113]},
                hp=30.0,
                spawned_x_offset=0.7,
                spawned_y_offset=0.7,
                spawn_color=Colors.GREEN
            ),

            # ==========================================
            # Zone Test Ground
            # ==========================================
            SpellData(
                spell_id=300,
                name="setup_test_zone",
                targeting=TargetingSpellMode.SELF,
                timeline={0: [69, 42]}
            ),
            SpellData(
                spell_id=9001,
                name="bravo_test_zone",
                targeting=TargetingSpellMode.SELF,
                timeline={0: [969, 42]}
            ),
        ]