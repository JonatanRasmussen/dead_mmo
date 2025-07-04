from src.config import AudioFiles, Colors, Consts
from src.models.components import Behavior, Controls, GameObj, Loadout, Position, Resources
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
        return SpellTemplates.apply_aura_to_self(215, NpcHealingPowerup.healing_burst_tick().spell_id, 15000, 150)

    @staticmethod
    def spawn_healing_powerup() -> SpellFactory:
        game_obj = GameObj(
            res=Resources(
                hp=30.0,
            ),
            pos=Position(
                x=0.2,
                y=-0.2,
            ),
            color=Colors.GREEN,
            loadout=Loadout(
                next_target_id=BasicTargeting.targetswap_to_parent().spell_id,
                ability_1_id=NpcHealingPowerup.healing_burst_apply().spell_id,
            )
        )
        obj_controls = (
            Controls(timeline_timestamp=100, swap_target=True),
            Controls(timeline_timestamp=200, ability_1=True),
        )
        return (
            SpellFactory(171)
            .spawn_minion(game_obj, obj_controls)
            .use_gcd()
            .set_audio(AudioFiles.REJUVENATION_APPLY)
        )