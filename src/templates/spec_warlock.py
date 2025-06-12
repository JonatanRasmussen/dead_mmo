from src.config import AudioFiles, Colors, Consts, SpriteFiles
from src.models import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.handlers.spell_factory import SpellFactory, SpellTemplates
from src.templates.basic_movement import BasicMovement
from src.templates.basic_targeting import BasicTargeting
from src.templates.basic_spawning import BasicSpawning
from src.templates.npc_healing_powerup import NpcHealingPowerup


class SpecWarlock:
    @staticmethod
    def fire_blast() -> SpellFactory:
        return (
            SpellTemplates.damage_current_target(111, 13.0)
            .use_gcd()
            .set_audio(AudioFiles.SHADOW_BOLT_HIT)
        )

    @staticmethod
    def fire_aura_tick() -> SpellFactory:
        return SpellTemplates.damage_enemies_within_range(112, 5.0, 0.2)

    @staticmethod
    def fire_aura_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(113, SpecWarlock.fire_aura_tick().spell_id, 3.0, 30)
    @staticmethod
    def shadowbolt_tick() -> SpellFactory:
        return (
            SpellTemplates.damage_current_target_when_within_range(116, 34.0, 0.05)
            .set_audio(AudioFiles.SHADOW_BOLT_HIT)
            .despawn_self()
        )
    @staticmethod
    def shadowbolt_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(117, SpecWarlock.shadowbolt_tick().spell_id, 30.0, 1200)
    @staticmethod
    def shadowbolt_spawn() -> SpellFactory:
        game_obj = GameObj(
            hp=7.0,
            x=0.5,
            y=0.5,
            movement_speed=5.0,
            color=Colors.WHITE,
            next_target_id=BasicTargeting.targetswap_to_parents_current_target().spell_id,
            ability_1_id=BasicMovement.teleport_to_parent().spell_id,
            ability_2_id=BasicMovement.start_move_towards_target().spell_id,
            ability_3_id=SpecWarlock.shadowbolt_apply().spell_id,
        )
        obj_controls = (
            Controls(timeline_timestamp=0.0, swap_target=True, ability_1=True),
            Controls(timeline_timestamp=0.001, ability_2=True, ability_3=True),
        )
        return (
            SpellFactory(41)
            .spawn_obj(game_obj)
            .add_controls(obj_controls)
            .use_gcd()
            .set_audio(AudioFiles.SHADOW_BOLT_CAST)
        )

    @staticmethod
    def spawn_player() -> SpellFactory:
        game_obj = GameObj(
            hp=30.0,
            x=0.3,
            y=0.3,
            color=Colors.RED,
            sprite_name=SpriteFiles.PORO_PLAYER,
            start_move_up_id=BasicMovement.start_move_up().spell_id,
            stop_move_up_id=BasicMovement.stop_move_up().spell_id,
            start_move_left_id=BasicMovement.start_move_left().spell_id,
            stop_move_left_id=BasicMovement.stop_move_left().spell_id,
            start_move_down_id=BasicMovement.start_move_down().spell_id,
            stop_move_down_id=BasicMovement.stop_move_down().spell_id,
            start_move_right_id=BasicMovement.start_move_right().spell_id,
            stop_move_right_id=BasicMovement.stop_move_right().spell_id,
            next_target_id=BasicTargeting.targetswap_to_next_tab_target().spell_id,
            ability_1_id=SpecWarlock.fire_blast().spell_id,
            ability_2_id=SpecWarlock.fire_aura_apply().spell_id,
            ability_3_id=NpcHealingPowerup.spawn_healing_powerup().spell_id,
            ability_4_id=SpecWarlock.shadowbolt_spawn().spell_id,
        )
        return (
            SpellFactory(42)
            .spawn_player(game_obj)
        )