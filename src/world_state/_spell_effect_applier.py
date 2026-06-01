from src.models.components import GameObj
from src.models.data import Behavior, Spell


class SpellEffectApplier:
    """Interprets spell behavior flags and applies effects to game objects.
    This is the ONLY place where Spell data causes GameObj mutation."""

    @staticmethod
    def apply_target_effects(spell: Spell, source: GameObj, target: GameObj) -> None:
        flags = spell.flags
        if flags & (Behavior.STEP_UP | Behavior.STEP_LEFT | Behavior.STEP_DOWN | Behavior.STEP_RIGHT):
            SpellEffectApplier._apply_movement(flags, target, spell.power)
        if flags & Behavior.DAMAGING:
            target.apply_damage(spell.power * source.spell_modifier)
        if flags & Behavior.HEALING:
            target.apply_healing(spell.power * source.spell_modifier)

    @staticmethod
    def apply_source_effects(spell: Spell, timestamp: int, source: GameObj, target: GameObj) -> None:
        flags = spell.flags
        if flags & Behavior.UPDATE_CURRENT_TARGET:
            source.set_current_target(target.obj_id)
        if flags & Behavior.TRIGGER_GCD:
            source.set_gcd_start(timestamp)
        if flags & Behavior.DESPAWN_SELF:
            source.despawn()
        if flags & Behavior.MOVE_TOWARDS_TARGET:
            source.move_towards_target(target)
        if flags & Behavior.TELEPORT_TO_TARGET:
            source.teleport_to_target(target)

    @staticmethod
    def _apply_movement(flags: Behavior, target: GameObj, power: float) -> None:
        speed = power * target.get_movement_speed()
        if flags & Behavior.STEP_UP:
            target.move_up(speed)
        if flags & Behavior.STEP_LEFT:
            target.move_left(speed)
        if flags & Behavior.STEP_DOWN:
            target.move_down(speed)
        if flags & Behavior.STEP_RIGHT:
            target.move_right(speed)