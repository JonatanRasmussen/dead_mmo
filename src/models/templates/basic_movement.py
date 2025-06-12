from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates


class BasicMovement:
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
            .cast_on_current_target()
            .add_flag(SpellFlag.MOVE_TOWARDS_TARGET)
        )
    @staticmethod
    def start_move_up() -> SpellFactory:
        return SpellTemplates.start_move_self(92, BasicMovement.step_up().spell_id)

    @staticmethod
    def start_move_left() -> SpellFactory:
        return SpellTemplates.start_move_self(182, BasicMovement.step_left().spell_id)

    @staticmethod
    def start_move_down() -> SpellFactory:
        return SpellTemplates.start_move_self(272, BasicMovement.step_down().spell_id)

    @staticmethod
    def start_move_right() -> SpellFactory:
        return SpellTemplates.start_move_self(2, BasicMovement.step_right().spell_id)

    @staticmethod
    def start_move_towards_target() -> SpellFactory:
        return SpellTemplates.start_move_self(362, BasicMovement.step_towards_target().spell_id)

    @staticmethod
    def stop_move_up() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(93, BasicMovement.start_move_up().spell_id)

    @staticmethod
    def stop_move_left() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(183, BasicMovement.start_move_left().spell_id)

    @staticmethod
    def stop_move_down() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(273, BasicMovement.start_move_down().spell_id)

    @staticmethod
    def stop_move_right() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(3, BasicMovement.start_move_right().spell_id)

    @staticmethod
    def stop_move_towards_target() -> SpellFactory:
        return SpellTemplates.cancel_aura_on_self(363, BasicMovement.start_move_towards_target().spell_id)

    @staticmethod
    def teleport_to_parent() -> SpellFactory:
        return (
            SpellFactory(451)
            .teleport_to_parent()
        )