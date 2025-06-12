from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates
from .basic_targeting import BasicTargeting


class NpcHealingPowerup:
    @staticmethod
    def healing_burst_tick() -> SpellFactory:
        return (
            SpellTemplates.heal_current_target_when_within_range(214, 150.0, 0.1)
            .despawn_self()
        )

    @staticmethod
    def healing_burst_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(215, NpcHealingPowerup.healing_burst_tick().spell_id, 15.0, 150)

    @staticmethod
    def spawn_healing_powerup() -> SpellFactory:
        game_obj = GameObj(
            hp=30.0,
            x=0.7,
            y=0.3,
            color=Colors.GREEN,
            next_target_id=BasicTargeting.targetswap_to_parent().spell_id,
            ability_1_id=NpcHealingPowerup.healing_burst_apply().spell_id,
        )
        obj_controls = (
            Controls(timeline_timestamp=0.1, swap_target=True),
            Controls(timeline_timestamp=0.2, ability_1=True),
        )
        return (
            SpellFactory(171)
            .spawn_obj(game_obj)
            .add_controls(obj_controls)
            .use_gcd()
            .set_audio(AudioFiles.REJUVENATION_APPLY)
        )