from src.config import AudioFiles, Colors, Consts
from src.models.components import Behavior, Controls, GameObj, Loadout, Position, Resources
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
            loadout=Loadout(
                next_target_id=BasicTargeting.targetswap_to_next_tab_target().spell_id,
                ability_3_id=SpecWarlock.fire_blast().spell_id,
                ability_4_id=BasicMovement.start_move_towards_target().spell_id,
            )
        )
        obj_controls = (
            Controls(timeline_timestamp=1500, swap_target=True),
            Controls(timeline_timestamp=4000, ability_3=True),
            Controls(timeline_timestamp=7000, ability_4=True),
        )
        return (
            SpellFactory(70)
            .spawn_boss(game_obj, obj_controls)
        )