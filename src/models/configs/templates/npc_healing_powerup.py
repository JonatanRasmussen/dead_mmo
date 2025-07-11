from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, Distance, GameObj, Faction, KeyPresses, Loadout, Position, Resources
from src.models.configs import Behavior, Targeting, Spell
from src.models.services import SpellFactory, SpellTemplates, GameObjFactory, GameObjTemplates
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
