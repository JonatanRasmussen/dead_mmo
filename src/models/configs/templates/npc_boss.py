from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, Faction, KeyPresses, Loadout, Position, Resources
from src.models.configs import Behavior, Targeting, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting
from .spec_warlock import SpecWarlock
from .npc_landmine import NpcLandmine
from .npc_target_dummy import NpcTargetDummy


class NpcBoss:
    @staticmethod
    def spawn_boss() -> SpellFactory:
        game_obj = GameObj(
            res=Resources(
                hp=30.0,
            ),
            pos=Position(
                x=0.7,
                y=0.7,
            ),
            color=Colors.GREEN,
            loadout=Loadout()
                .bind_spell(KeyPresses.SWAP_TARGET, BasicTargeting.targetswap_to_next_tab_target().spell_id)
                .bind_spell(KeyPresses.ABILITY_1, SpecWarlock.fire_blast().spell_id)
                .bind_spell(KeyPresses.ABILITY_2, SpecWarlock.fire_aura_apply().spell_id)
                .bind_spell(KeyPresses.ABILITY_3, NpcTargetDummy.spawn_target_dummy().spell_id)
                .bind_spell(KeyPresses.ABILITY_4, NpcLandmine.spawn_landmine().spell_id)
        )
        obj_controls = (
            Controls(timeline_timestamp=400, key_presses=KeyPresses.ABILITY_3),
            Controls(timeline_timestamp=800, key_presses=KeyPresses.ABILITY_4),
            Controls(timeline_timestamp=1000, key_presses=KeyPresses.SWAP_TARGET),
            Controls(timeline_timestamp=3000, key_presses=KeyPresses.ABILITY_1),
            Controls(timeline_timestamp=5000, key_presses=KeyPresses.ABILITY_2),
        )
        return (
            SpellFactory(69)
            .spawn_boss(game_obj, obj_controls)
        )