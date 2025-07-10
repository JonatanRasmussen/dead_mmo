from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, Faction, KeyPresses, Loadout, Position, Resources
from src.models.configs import Behavior, Targeting, Spell
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
            loadout=Loadout()
                .bind_spell(KeyPresses.SWAP_TARGET, BasicTargeting.targetswap_to_parent().spell_id)
                .bind_spell(KeyPresses.ABILITY_1, NpcHealingPowerup.healing_burst_apply().spell_id)
        )
        obj_controls = (
            Controls(timeline_timestamp=100, key_presses=KeyPresses.SWAP_TARGET),
            Controls(timeline_timestamp=200, key_presses=KeyPresses.ABILITY_1),
        )
        return (
            SpellFactory(171)
            .spawn_minion(game_obj, obj_controls)
            .use_gcd()
            .set_audio(AudioFiles.REJUVENATION_APPLY)
        )