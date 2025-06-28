from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, Behavior, Targeting, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting
from .basic_spawning import BasicSpawning
from .spec_warlock import SpecWarlock
from .npc_landmine import NpcLandmine
from .npc_target_dummy import NpcTargetDummy


class NpcBoss:
    @staticmethod
    def spawn_boss() -> SpellFactory:
        game_obj = GameObj(
            hp=30.0,
            x=0.7,
            y=0.7,
            color=Colors.GREEN,
            next_target_id=BasicTargeting.targetswap_to_next_tab_target().spell_id,
            ability_1_id=SpecWarlock.fire_blast().spell_id,
            ability_2_id=SpecWarlock.fire_aura_apply().spell_id,
            ability_3_id=NpcTargetDummy.spawn_target_dummy().spell_id,
            ability_4_id=NpcLandmine.spawn_landmine().spell_id,
        )
        obj_controls = (
            Controls(timeline_timestamp=0.4, ability_3=True),
            Controls(timeline_timestamp=0.8, ability_4=True),
            Controls(timeline_timestamp=1.0, swap_target=True),
            Controls(timeline_timestamp=3.0, ability_1=True),
            Controls(timeline_timestamp=5.0, ability_2=True),
        )
        return (
            SpellFactory(69)
            .spawn_boss(game_obj)
            .add_controls(obj_controls)
        )