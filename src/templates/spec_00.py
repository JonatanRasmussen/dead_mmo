from src.models.spell import SpellFlag, SpellTarget, Spell, IdGen
from src.templates.spell_factory import SpellFactory, SpellTemplates
from src.config.color import Color
from src.models.controls import Controls
from src.models.game_obj import GameObj


class Spec00:
    @staticmethod
    def empty_spell() -> SpellFactory:
        return (
            SpellFactory(IdGen.EMPTY_ID)
        )

    @staticmethod
    def despawn_self() -> SpellFactory:
        return (
            SpellFactory(33)
            .self_cast()
            .add_flag(SpellFlag.DESPAWN_SELF)
        )

    @staticmethod
    def tab_target() -> SpellFactory:
        return (
            SpellFactory(15)
            .target_swap()
        )

    @staticmethod
    def step_up() -> SpellFactory:
        return SpellTemplates.step_move_self(91, SpellFlag.STEP_UP)

    @staticmethod
    def step_left() -> SpellFactory:
        return SpellTemplates.step_move_self(181, SpellFlag.STEP_LEFT)

    @staticmethod
    def step_down() -> SpellFactory:
        return SpellTemplates.step_move_self(271, SpellFlag.STEP_DOWN)

    @staticmethod
    def step_right() -> SpellFactory:
        return SpellTemplates.step_move_self(1, SpellFlag.STEP_RIGHT)

    @staticmethod
    def step_towards_target() -> SpellFactory:
        return (
            SpellFactory(361)
            .target_cast()
            .add_flag(SpellFlag.MOVE_TOWARDS_TARGET)
        )
    @staticmethod
    def start_move_up() -> SpellFactory:
        return SpellTemplates.start_move_self(92, Spec00.step_up().spell_id)

    @staticmethod
    def start_move_left() -> SpellFactory:
        return SpellTemplates.start_move_self(182, Spec00.step_left().spell_id)

    @staticmethod
    def start_move_down() -> SpellFactory:
        return SpellTemplates.start_move_self(272, Spec00.step_down().spell_id)

    @staticmethod
    def start_move_right() -> SpellFactory:
        return SpellTemplates.start_move_self(2, Spec00.step_right().spell_id)

    @staticmethod
    def start_move_towards_target() -> SpellFactory:
        return SpellTemplates.start_move_self(362, Spec00.step_towards_target().spell_id)

    @staticmethod
    def stop_move_up() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(93, Spec00.start_move_up().spell_id)

    @staticmethod
    def stop_move_left() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(183, Spec00.start_move_left().spell_id)

    @staticmethod
    def stop_move_down() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(273, Spec00.start_move_down().spell_id)

    @staticmethod
    def stop_move_right() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(3, Spec00.start_move_right().spell_id)

    @staticmethod
    def stop_move_towards_target() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(363, Spec00.start_move_towards_target().spell_id)


    @staticmethod
    def fire_blast() -> SpellFactory:
        return (
            SpellTemplates.damage_current_target(111, 13.0)
            .use_gcd()
        )

    @staticmethod
    def fire_aura_tick() -> SpellFactory:
        return SpellTemplates.damage_enemies_within_range(112, 5.0, 0.2)

    @staticmethod
    def fire_aura_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(113, Spec00.fire_aura_tick().spell_id, 3.0, 30)

    @staticmethod
    def fire_explosion_tick() -> SpellFactory:
        return (
            SpellTemplates.damage_enemies_within_range(114, 150.0, 0.1)
            .despawn_self()
        )

    @staticmethod
    def fire_explosion_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(115, Spec00.fire_explosion_tick().spell_id, 15.0, 150)

    @staticmethod
    def spawn_player() -> SpellFactory:
        game_obj = GameObj(
            hp=30.0,
            x=0.3,
            y=0.3,
            color=Color.RED,
            start_move_up_id=Spec00.start_move_up().spell_id,
            stop_move_up_id=Spec00.stop_move_up().spell_id,
            start_move_left_id=Spec00.start_move_left().spell_id,
            stop_move_left_id=Spec00.stop_move_left().spell_id,
            start_move_down_id=Spec00.start_move_down().spell_id,
            stop_move_down_id=Spec00.stop_move_down().spell_id,
            start_move_right_id=Spec00.start_move_right().spell_id,
            stop_move_right_id=Spec00.stop_move_right().spell_id,
            next_target_id=Spec00.tab_target().spell_id,
            ability_1_id=Spec00.fire_blast().spell_id,
            ability_2_id=Spec00.fire_aura_apply().spell_id,
            ability_3_id=Spec00.start_move_towards_target().spell_id,
            ability_4_id=Spec00.stop_move_towards_target().spell_id,
        )
        return (
            SpellFactory(42)
            .spawn_player(game_obj)
        )

    @staticmethod
    def spawn_boss() -> SpellFactory:
        game_obj = GameObj(
            hp=30.0,
            x=0.7,
            y=0.7,
            color=Color.GREEN,
            next_target_id=Spec00.tab_target().spell_id,
            ability_1_id=Spec00.fire_blast().spell_id,
            ability_2_id=Spec00.fire_aura_apply().spell_id,
        )
        obj_controls = (
            Controls(timestamp=1.0, next_target=True),
            Controls(timestamp=3.0, ability_1=True),
            Controls(timestamp=5.0, ability_2=True),
        )
        return (
            SpellFactory(69)
            .spawn_boss(game_obj)
            .add_controls(obj_controls)
        )

    @staticmethod
    def spawn_target_dummy() -> SpellFactory:
        game_obj = GameObj(
            hp=80.0,
            x=0.5,
            y=0.8,
            color=Color.BLUE,
            next_target_id=Spec00.tab_target().spell_id,
            ability_3_id=Spec00.fire_blast().spell_id,
            ability_4_id=Spec00.start_move_towards_target().spell_id,
        )
        obj_controls = (
            Controls(timestamp=1.5, next_target=True),
            Controls(timestamp=4.0, ability_3=True),
            Controls(timestamp=7.0, ability_4=True),
        )
        return (
            SpellFactory(70)
            .spawn_boss(game_obj)
            .add_controls(obj_controls)
        )

    @staticmethod
    def spawn_landmine() -> SpellFactory:
        game_obj = GameObj(
            hp=20.0,
            x=0.2,
            y=0.8,
            color=Color.MAGENTA,
            ability_1_id=Spec00.fire_explosion_apply().spell_id,
        )
        obj_controls = (
            Controls(timestamp=1.5, ability_1=True),
        )
        return (
            SpellFactory(71)
            .spawn_enemy_obj(game_obj)
            .add_controls(obj_controls)
        )

    @staticmethod
    def setup_test_zone() -> SpellFactory:
        spell_sequence = (
            Spec00.spawn_boss().spell_id,
            Spec00.spawn_target_dummy().spell_id,
            Spec00.spawn_player().spell_id,
            Spec00.spawn_landmine().spell_id,
        )
        return (
            SpellFactory(300)
            .self_cast()
            .set_spell_sequence(spell_sequence)
        )
