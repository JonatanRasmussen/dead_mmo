from src.config import AudioFiles, Colors, Consts, SpriteFiles
from src.models.components import Controls, GameObj, Faction, KeyPresses, Loadout, Position, Resources, BaseStats, Visuals
from src.models.configs import Behavior, Targeting, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting
from .npc_healing_powerup import NpcHealingPowerup


class SpecWarlock:
    @staticmethod
    def fire_blast() -> SpellFactory:
        return (
            SpellTemplates.damage_current_target(111, 13.0)
            .aoe_cast()
            .use_gcd()
            .set_audio(AudioFiles.SHADOW_BOLT_HIT)
        )

    @staticmethod
    def fire_aura_tick() -> SpellFactory:
        return SpellTemplates.damage_enemies_within_range(112, 5.0, 0.2)

    @staticmethod
    def fire_aura_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(113, SpecWarlock.fire_aura_tick().spell_id, 3000, 30)
    @staticmethod
    def shadowbolt_tick() -> SpellFactory:
        return (
            SpellTemplates.damage_current_target_when_within_range(116, 34.0, 0.05)
            .set_audio(AudioFiles.SHADOW_BOLT_HIT)
            .despawn_self()
        )
    @staticmethod
    def aura_shadowbolt() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(117, SpecWarlock.shadowbolt_tick().spell_id, 30000, 1200)
    @staticmethod
    def shadowbolt_spawn() -> SpellFactory:
        game_obj = GameObj(
            res=Resources(
                hp=7.0,
            ),
            pos=Position(
                x=0.0,
                y=0.05,
            ),
            stats=BaseStats(
                movement_speed=5.0
            ),
            color=Colors.WHITE,
            loadout=Loadout()
                .bind_spell(KeyPresses.ABILITY_1, BasicMovement.start_move_towards_target().spell_id)
                .bind_spell(KeyPresses.ABILITY_2, SpecWarlock.aura_shadowbolt().spell_id)
        )
        obj_controls = (
            Controls(timeline_timestamp=0, key_presses=KeyPresses.ABILITY_1 | KeyPresses.ABILITY_2),
        )
        return (
            SpellFactory(41)
            .spawn_projectile(game_obj, obj_controls)
            .aoe_cast()
            .use_gcd()
            .set_audio(AudioFiles.SHADOW_BOLT_CAST)
        )

    @staticmethod
    def spawn_player() -> SpellFactory:
        game_obj = GameObj(
            res=Resources(
                hp=30.0,
            ),
            pos=Position(
                x=0.3,
                y=0.3,
            ),
            color=Colors.RED,
            sprite_name=SpriteFiles.PORO_PLAYER,
            loadout = Loadout()
                .bind_spell(KeyPresses.START_MOVE_UP, BasicMovement.start_move_up().spell_id)
                .bind_spell(KeyPresses.STOP_MOVE_UP, BasicMovement.stop_move_up().spell_id)
                .bind_spell(KeyPresses.START_MOVE_LEFT, BasicMovement.start_move_left().spell_id)
                .bind_spell(KeyPresses.STOP_MOVE_LEFT, BasicMovement.stop_move_left().spell_id)
                .bind_spell(KeyPresses.START_MOVE_DOWN, BasicMovement.start_move_down().spell_id)
                .bind_spell(KeyPresses.STOP_MOVE_DOWN, BasicMovement.stop_move_down().spell_id)
                .bind_spell(KeyPresses.START_MOVE_RIGHT, BasicMovement.start_move_right().spell_id)
                .bind_spell(KeyPresses.STOP_MOVE_RIGHT, BasicMovement.stop_move_right().spell_id)
                .bind_spell(KeyPresses.SWAP_TARGET, BasicTargeting.targetswap_to_next_tab_target().spell_id)
                .bind_spell(KeyPresses.ABILITY_1, SpecWarlock.fire_blast().spell_id)
                .bind_spell(KeyPresses.ABILITY_2, SpecWarlock.fire_aura_apply().spell_id)
                .bind_spell(KeyPresses.ABILITY_3, NpcHealingPowerup.spawn_healing_powerup().spell_id)
                .bind_spell(KeyPresses.ABILITY_4, SpecWarlock.shadowbolt_spawn().spell_id)
        )
        return (
            SpellFactory(42)
            .spawn_player(game_obj)
        )