from src.settings import AudioFiles, Colors, Consts, SpriteFiles
from src.world_state import Behavior, KeyPresses, Loadout
from src.world_state._spell_factories import SpellFactory, SpellTemplates, GameObjTemplates


class BasicMovement:
    @staticmethod
    def empty_spell() -> SpellFactory:
        return SpellFactory(Consts.EMPTY_ID)

    @staticmethod
    def step_up() -> SpellFactory:
        return SpellTemplates.step_move_self(91, Behavior.STEP_UP)

    @staticmethod
    def step_left() -> SpellFactory:
        return SpellTemplates.step_move_self(181, Behavior.STEP_LEFT)

    @staticmethod
    def step_down() -> SpellFactory:
        return SpellTemplates.step_move_self(271, Behavior.STEP_DOWN)

    @staticmethod
    def step_right() -> SpellFactory:
        return SpellTemplates.step_move_self(1, Behavior.STEP_RIGHT)

    @staticmethod
    def step_towards_target() -> SpellFactory:
        return SpellFactory(361).cast_on_target().add_flag(Behavior.MOVE_TOWARDS_TARGET)

    @staticmethod
    def start_move_up() -> SpellFactory:
        return SpellTemplates.start_move_self(92, BasicMovement.step_up().spell_id).add_flag(Behavior.STEP_UP)

    @staticmethod
    def start_move_left() -> SpellFactory:
        return SpellTemplates.start_move_self(182, BasicMovement.step_left().spell_id).add_flag(Behavior.STEP_LEFT)

    @staticmethod
    def start_move_down() -> SpellFactory:
        return SpellTemplates.start_move_self(272, BasicMovement.step_down().spell_id).add_flag(Behavior.STEP_DOWN)

    @staticmethod
    def start_move_right() -> SpellFactory:
        return SpellTemplates.start_move_self(2, BasicMovement.step_right().spell_id).add_flag(Behavior.STEP_RIGHT)

    @staticmethod
    def start_move_towards_target() -> SpellFactory:
        return SpellTemplates.start_move_self(362, BasicMovement.step_towards_target().spell_id).add_flag(Behavior.MOVE_TOWARDS_TARGET)

    @staticmethod
    def stop_move_up() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(93, BasicMovement.start_move_up().spell_id).add_flag(Behavior.STOP_MOVE_UP)

    @staticmethod
    def stop_move_left() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(183, BasicMovement.start_move_left().spell_id).add_flag(Behavior.STOP_MOVE_LEFT)

    @staticmethod
    def stop_move_down() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(273, BasicMovement.start_move_down().spell_id).add_flag(Behavior.STOP_MOVE_DOWN)

    @staticmethod
    def stop_move_right() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(3, BasicMovement.start_move_right().spell_id).add_flag(Behavior.STOP_MOVE_RIGHT)

    @staticmethod
    def stop_move_towards_target() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(363, BasicMovement.start_move_towards_target().spell_id).add_flag(Behavior.STOP_MOVE_TOWARDS_TARGET)

class BasicTargeting:
    @staticmethod
    def targetswap_to_next_tab_target() -> SpellFactory:
        return (
            SpellFactory(15)
            .cast_on_next_tab_target()
            .update_current_target()
        )
    @staticmethod
    def targetswap_to_parent() -> SpellFactory:
        return (
            SpellFactory(16)
            .cast_on_parent()
            .update_current_target()
        )

class NpcHealingPowerup:
    @staticmethod
    def healing_burst_tick() -> SpellFactory:
        return (
            SpellTemplates.heal_current_target_when_within_range(214, 150.0, 0.1)
            .despawn_self()
        )

    @staticmethod
    def healing_burst_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(215, NpcHealingPowerup.healing_burst_tick().spell_id, 15000, 150)

    @staticmethod
    def spawn_healing_powerup() -> SpellFactory:
        timeline = {
            100: BasicTargeting.targetswap_to_parent().spell_id,
            200: NpcHealingPowerup.healing_burst_apply().spell_id,
        }
        obj_template = GameObjTemplates.create_enemy(timeline, x=0.2, y=-0.2, hp=30.0, color=Colors.GREEN)
        return (
            SpellFactory(171)
            .spawn_minion(obj_template)
            .use_gcd()
            .set_audio(AudioFiles.REJUVENATION_APPLY)
        )

class NpcLandmine:
    @staticmethod
    def landmine_explosion_tick() -> SpellFactory:
        return (
            SpellTemplates.damage_enemies_within_range(114, 150.0, 0.1)
            .despawn_self()
        )

    @staticmethod
    def landmine_explosion_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(115, NpcLandmine.landmine_explosion_tick().spell_id, 15000, 150)

    @staticmethod
    def spawn_landmine() -> SpellFactory:
        timeline = {1500: NpcLandmine.landmine_explosion_apply().spell_id}
        obj_template = GameObjTemplates.create_enemy(timeline, x=-0.5, y=0.1, hp=20.0, color=Colors.MAGENTA)
        return (
            SpellFactory(71)
            .spawn_minion(obj_template)
        )

class NpcTargetDummy:
    @staticmethod
    def spawn_target_dummy() -> SpellFactory:
        timeline = {
            1500: BasicTargeting.targetswap_to_next_tab_target().spell_id,
            4000: SpecWarlock.fire_blast().spell_id,
            7000: BasicMovement.start_move_towards_target().spell_id,
        }
        obj_template = GameObjTemplates.create_enemy(timeline, x=-0.2, y=0.1, hp=80.0, color=Colors.BLUE)
        return (
            SpellFactory(70)
            .spawn_boss(obj_template)
        )

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
        timeline = {0: (
            BasicMovement.start_move_towards_target().spell_id,
            SpecWarlock.aura_shadowbolt().spell_id
        )}
        obj_template = GameObjTemplates.create_projectile(timeline, speed=5.0, size=7.0, color=Colors.WHITE)
        return (
            SpellFactory(41)
            .spawn_projectile(obj_template)
            .aoe_cast()
            .use_gcd()
            .set_audio(AudioFiles.SHADOW_BOLT_CAST)
        )

    @staticmethod
    def spawn_player() -> SpellFactory:
        loadout = (
            Loadout()
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
        obj_template = GameObjTemplates.create_player(loadout, x=0.3, y=0.3, hp=30.0, color=Colors.RED, sprite_name=SpriteFiles.PORO_PLAYER)
        return (
            SpellFactory(42)
            .spawn_player(obj_template)
        )

class NpcBoss:
    @staticmethod
    def spawn_boss() -> SpellFactory:
        timeline = {
            400: NpcTargetDummy.spawn_target_dummy().spell_id,
            800: NpcLandmine.spawn_landmine().spell_id,
            1000: BasicTargeting.targetswap_to_next_tab_target().spell_id,
            3000: SpecWarlock.fire_blast().spell_id,
            5000: SpecWarlock.fire_aura_apply().spell_id,
        }
        obj_template = GameObjTemplates.create_enemy(timeline, x=0.7, y=0.7, hp=30.0, color=Colors.GREEN)
        return (
            SpellFactory(69)
            .spawn_boss(obj_template)
        )

class ZoneTestGround:
    @staticmethod
    def setup_test_zone() -> SpellFactory:
        spell_sequence = (
            NpcBoss.spawn_boss().spell_id,
            SpecWarlock.spawn_player().spell_id,
        )
        return (
            SpellFactory(300)
            .cast_on_self()
            .set_spell_sequence(spell_sequence)
        )
