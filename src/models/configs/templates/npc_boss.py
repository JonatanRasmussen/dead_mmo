from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, Distance, GameObj, Faction, KeyPresses, Loadout, Position, Resources
from src.models.configs import Behavior, Targeting, Spell
from src.models.services import SpellFactory, SpellTemplates, GameObjFactory, GameObjTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting
from .spec_warlock import SpecWarlock
from .npc_landmine import NpcLandmine
from .npc_target_dummy import NpcTargetDummy


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