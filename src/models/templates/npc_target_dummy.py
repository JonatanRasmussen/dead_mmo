from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.models.services.spell_factory import SpellFactory, SpellTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting
from .basic_spawning import BasicSpawning
from .spec_warlock import SpecWarlock


class NpcTargetDummy:
    @staticmethod
    def spawn_target_dummy() -> SpellFactory:
        game_obj = GameObj(
            hp=80.0,
            x=0.5,
            y=0.8,
            color=Colors.BLUE,
            next_target_id=BasicTargeting.targetswap_to_next_tab_target().spell_id,
            ability_3_id=SpecWarlock.fire_blast().spell_id,
            ability_4_id=BasicMovement.start_move_towards_target().spell_id,
        )
        obj_controls = (
            Controls(timeline_timestamp=1.5, swap_target=True),
            Controls(timeline_timestamp=4.0, ability_3=True),
            Controls(timeline_timestamp=7.0, ability_4=True),
        )
        return (
            SpellFactory(70)
            .spawn_boss(game_obj)
            .add_controls(obj_controls)
        )