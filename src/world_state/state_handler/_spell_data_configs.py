from src.settings import AudioFiles, Colors, Consts, SpriteFiles
from ._spell_data import SpellData
from ._casting_system import CastingBehavior, Controls, KeyPresses
from ._health_system import HealthBehavior
from ._movement_system import MovementBehavior
from ._targeting_system import TargetingBehavior, Targeting


class LegacySpellConfig:
    """A completely flattened, explicit list of all spells in the game."""

    @staticmethod
    def get_all_spells() -> list[SpellData]:
        # Helper to pad spell_bindings array to the required 13 slots
        def pad(b: list[int]) -> list[int]:
            return b + [Consts.EMPTY_ID] * (13 - len(b))

        return [
            # ==========================================
            # Basic Movement
            # ==========================================
            SpellData(
                spell_id=Consts.EMPTY_ID,
            ),
            SpellData(
                spell_id=91,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.MOVE_UP
            ),
            SpellData(
                spell_id=92,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.STOP_MOVE_UP
            ),
            SpellData(
                spell_id=181,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.MOVE_LEFT
            ),
            SpellData(
                spell_id=182,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.STOP_MOVE_LEFT
            ),
            SpellData(
                spell_id=271,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.MOVE_DOWN
            ),
            SpellData(
                spell_id=272,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.STOP_MOVE_DOWN
            ),
            SpellData(
                spell_id=1,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.MOVE_RIGHT
            ),
            SpellData(
                spell_id=2,
                targeting=Targeting.SELF,
                movement_behavior=MovementBehavior.STOP_MOVE_RIGHT
            ),
            SpellData(
                spell_id=361,
                targeting=Targeting.TARGET,
                movement_behavior=MovementBehavior.MOVE_TOWARDS_TARGET
            ),
            SpellData(
                spell_id=362,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.START_CHANNEL,
                movement_behavior=MovementBehavior.MOVE_TOWARDS_TARGET,
                effect_id=361,
                duration=60000,
                ticks=60 * Consts.MOVEMENT_UPDATES_PER_SECOND
            ),
            SpellData(
                spell_id=363,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.STOP_CHANNEL,
                movement_behavior=MovementBehavior.STOP_MOVE_TOWARDS_TARGET
            ),

            # ==========================================
            # Basic Targeting
            # ==========================================
            SpellData(
                spell_id=15,
                targeting=Targeting.TAB_TO_NEXT,
                targeting_behavior=TargetingBehavior.UPDATE_CURRENT_TARGET
            ),
            SpellData(
                spell_id=16,
                targeting=Targeting.PARENT,
                targeting_behavior=TargetingBehavior.UPDATE_CURRENT_TARGET
            ),

            # ==========================================
            # Npc Healing Powerup
            # ==========================================
            SpellData(
                spell_id=214,
                targeting=Targeting.TARGET,
                movement_behavior=MovementBehavior.DESPAWN_SELF,
                health_behavior=HealthBehavior.HEALING,
                targeting_behavior=TargetingBehavior.DESPAWN_SELF,
                power=150.0,
                range_limit=0.1
            ),
            SpellData(
                spell_id=215,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.START_CHANNEL,
                effect_id=214,
                duration=15000,
                ticks=150
            ),
            SpellData(
                spell_id=171,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.TRIGGER_GCD,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ,
                timeline={100: 16, 200: 215},
                spell_bindings=pad([16, 215]),
                controls=(
                    Controls(timeline_timestamp=100, key_presses=KeyPresses.ABILITY_1),
                    Controls(timeline_timestamp=200, key_presses=KeyPresses.ABILITY_2)
                ),
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
                targeting=Targeting.DEFAULT_ENEMY,
                movement_behavior=MovementBehavior.DESPAWN_SELF,
                health_behavior=HealthBehavior.DAMAGING,
                targeting_behavior=TargetingBehavior.DESPAWN_SELF,
                power=150.0,
                range_limit=0.1
            ),
            SpellData(
                spell_id=115,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.START_CHANNEL,
                effect_id=114,
                duration=15000,
                ticks=150
            ),
            SpellData(
                spell_id=71,
                targeting=Targeting.SELF,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ,
                timeline={1500: 115},
                spell_bindings=pad([115]),
                controls=(
                    Controls(timeline_timestamp=1500, key_presses=KeyPresses.ABILITY_1),
                ),
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
                targeting=Targeting.SELF,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ | TargetingBehavior.SPAWN_BOSS,
                timeline={1500: 15, 4000: 128, 7000: 362},
                spell_bindings=pad([15, 128, 362]),
                controls=(
                    Controls(timeline_timestamp=1500, key_presses=KeyPresses.ABILITY_1),
                    Controls(timeline_timestamp=4000, key_presses=KeyPresses.ABILITY_2),
                    Controls(timeline_timestamp=7000, key_presses=KeyPresses.ABILITY_3),
                ),
                hp=80.0,
                spawned_x_offset=-0.2,
                spawned_y_offset=0.1,
                spawn_color=Colors.BLUE
            ),
            SpellData(
                spell_id=970,
                targeting=Targeting.SELF,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ | TargetingBehavior.SPAWN_BOSS,
                timeline={1500: 15, 2000: 941, 4000: 124, 7000: 362},
                spell_bindings=pad([15, 124, 362, 941]),
                controls=(
                    Controls(timeline_timestamp=1500, key_presses=KeyPresses.ABILITY_1),
                    Controls(timeline_timestamp=2000, key_presses=KeyPresses.ABILITY_4),
                    Controls(timeline_timestamp=4000, key_presses=KeyPresses.ABILITY_2),
                    Controls(timeline_timestamp=7000, key_presses=KeyPresses.ABILITY_3),
                ),
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
                targeting=Targeting.TARGET,
                casting_behavior=CastingBehavior.TRIGGER_GCD,
                targeting_behavior=TargetingBehavior.AOE,
                effect_id=111
            ),
            SpellData(
                spell_id=111,
                targeting=Targeting.USE_EVENT_TARGET,
                health_behavior=HealthBehavior.DAMAGING,
                power=13.0,
                audio_name=AudioFiles.SHADOW_BOLT_HIT
            ),
            SpellData(
                spell_id=911,
                targeting=Targeting.TARGET,
                health_behavior=HealthBehavior.DAMAGING,
                power=53.0,
                audio_name=AudioFiles.SHADOW_BOLT_BUILD
            ),
            SpellData(
                spell_id=112,
                targeting=Targeting.DEFAULT_ENEMY,
                health_behavior=HealthBehavior.DAMAGING,
                power=5.0,
                range_limit=0.2
            ),
            SpellData(
                spell_id=113,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.START_CHANNEL,
                effect_id=112,
                duration=3000,
                ticks=30
            ),
            SpellData(
                spell_id=131,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.START_CHANNEL,
                effect_id=132,
                duration=60000,
                ticks=60 * Consts.MOVEMENT_UPDATES_PER_SECOND
            ),
            SpellData(
                spell_id=132,
                targeting=Targeting.SELF,
                spell_sequence=(133, 116)
            ),
            SpellData(
                spell_id=116,
                targeting=Targeting.TARGET,
                movement_behavior=MovementBehavior.DESPAWN_SELF,
                health_behavior=HealthBehavior.DAMAGING,
                targeting_behavior=TargetingBehavior.DESPAWN_SELF,
                power=34.0,
                range_limit=0.05,
                audio_name=AudioFiles.SHADOW_BOLT_HIT
            ),
            SpellData(
                spell_id=133,
                targeting=Targeting.TARGET,
                movement_behavior=MovementBehavior.MOVE_TOWARDS_TARGET
            ),
            SpellData(
                spell_id=124,
                targeting=Targeting.TARGET,
                casting_behavior=CastingBehavior.TRIGGER_GCD,
                targeting_behavior=TargetingBehavior.AOE,
                effect_id=41
            ),
            SpellData(
                spell_id=41,
                targeting=Targeting.USE_EVENT_TARGET,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ,
                timeline={0: 131},
                spell_bindings=pad([131]),
                controls=(
                    Controls(timeline_timestamp=0, key_presses=KeyPresses.ABILITY_1),
                ),
                spawned_x_offset=0.0,
                spawned_y_offset=0.05,
                spawned_movespeed=5.0,
                audio_name=AudioFiles.SHADOW_BOLT_CAST,
                spawn_color=Colors.WHITE
            ),
            SpellData(
                spell_id=941,
                targeting=Targeting.SELF,
                casting_behavior=CastingBehavior.START_CHANNEL,
                effect_id=911,
                duration=1220,
                ticks=4
            ),
            SpellData(
                spell_id=42,
                targeting=Targeting.SELF,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ | TargetingBehavior.SPAWN_PLAYER,
                spell_bindings=[128, 113, 171, 124, 15, 91, 92, 181, 182, 271, 272, 1, 2],
                controls=(),
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
                targeting=Targeting.SELF,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ | TargetingBehavior.SPAWN_BOSS,
                timeline={400: 70, 800: 71, 1000: 15, 3000: 128, 5000: 113},
                spell_bindings=pad([15, 70, 71, 113, 128]),
                controls=(
                    Controls(timeline_timestamp=400, key_presses=KeyPresses.ABILITY_2),
                    Controls(timeline_timestamp=800, key_presses=KeyPresses.ABILITY_3),
                    Controls(timeline_timestamp=1000, key_presses=KeyPresses.ABILITY_1),
                    Controls(timeline_timestamp=3000, key_presses=KeyPresses.SWAP_TARGET),
                    Controls(timeline_timestamp=5000, key_presses=KeyPresses.ABILITY_4),
                ),
                hp=30.0,
                spawned_x_offset=0.7,
                spawned_y_offset=0.7,
                spawn_color=Colors.GREEN
            ),
            SpellData(
                spell_id=969,
                targeting=Targeting.SELF,
                targeting_behavior=TargetingBehavior.SPAWN_OBJ | TargetingBehavior.SPAWN_BOSS,
                timeline={400: 970, 800: 71, 1000: 15, 3000: 128, 5000: 113},
                spell_bindings=pad([15, 71, 113, 128, 970]),
                controls=(
                    Controls(timeline_timestamp=400, key_presses=KeyPresses.SWAP_TARGET),
                    Controls(timeline_timestamp=800, key_presses=KeyPresses.ABILITY_2),
                    Controls(timeline_timestamp=1000, key_presses=KeyPresses.ABILITY_1),
                    Controls(timeline_timestamp=3000, key_presses=KeyPresses.ABILITY_4),
                    Controls(timeline_timestamp=5000, key_presses=KeyPresses.ABILITY_3),
                ),
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
                targeting=Targeting.SELF,
                spell_sequence=(69, 42)
            ),
            SpellData(
                spell_id=9001,
                targeting=Targeting.SELF,
                spell_sequence=(969, 42)
            ),
        ]