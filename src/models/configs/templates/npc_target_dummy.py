from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, Faction, KeyPresses, Loadout, Position, Resources
from src.models.configs import Behavior, Targeting, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting
from .spec_warlock import SpecWarlock


class NpcTargetDummy:
    @staticmethod
    def spawn_target_dummy() -> SpellFactory:
        game_obj = GameObj(
            res=Resources(
                hp=80.0,
            ),
            pos=Position(
                x=-0.2,
                y=0.1,
            ),
            color=Colors.BLUE,
            loadout=Loadout()
                .bind_spell(KeyPresses.SWAP_TARGET, BasicTargeting.targetswap_to_next_tab_target().spell_id)
                .bind_spell(KeyPresses.ABILITY_3, SpecWarlock.fire_blast().spell_id)
                .bind_spell(KeyPresses.ABILITY_4, BasicMovement.start_move_towards_target().spell_id)
        )
        obj_controls = (
            Controls(timeline_timestamp=1500, key_presses=KeyPresses.SWAP_TARGET),
            Controls(timeline_timestamp=4000, key_presses=KeyPresses.ABILITY_3),
            Controls(timeline_timestamp=7000, key_presses=KeyPresses.ABILITY_4),
        )
        return (
            SpellFactory(70)
            .spawn_boss(game_obj, obj_controls)
        )