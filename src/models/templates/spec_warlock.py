from src.config import AudioFiles, Colors, Consts, SpriteFiles
from src.models.components import Behavior, Controls, GameObj, Loadout, Modifiers, Position, Resources, Views
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
        return SpellTemplates.apply_aura_to_self(113, SpecWarlock.fire_aura_tick().spell_id, 3.0, 30)
    @staticmethod
    def shadowbolt_tick() -> SpellFactory:
        return (
            SpellTemplates.damage_current_target_when_within_range(116, 34.0, 0.05)
            .set_audio(AudioFiles.SHADOW_BOLT_HIT)
            .despawn_self()
        )
    @staticmethod
    def aura_shadowbolt() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(117, SpecWarlock.shadowbolt_tick().spell_id, 30.0, 1200)
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
            mods=Modifiers(
                movement_speed=5.0
            ),
            color=Colors.WHITE,
            loadout=Loadout(
                ability_1_id=BasicMovement.start_move_towards_target().spell_id,
                ability_2_id=SpecWarlock.aura_shadowbolt().spell_id,
            )
        )
        obj_controls = (
            Controls(timeline_timestamp=0.0, ability_1=True, ability_2=True),
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
            views=Views(
                sprite_name=SpriteFiles.PORO_PLAYER,
            ),
            loadout=Loadout(
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
        )
        return (
            SpellFactory(42)
            .spawn_player(game_obj)
        )