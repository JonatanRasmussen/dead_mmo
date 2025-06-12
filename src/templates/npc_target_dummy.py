from src.config import AudioFiles, Colors, Consts
from src.models import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.handlers.spell_factory import SpellFactory, SpellTemplates
from src.templates.basic_movement import BasicMovement
from src.templates.basic_targeting import BasicTargeting
from src.templates.basic_spawning import BasicSpawning
from src.templates.spec_warlock import SpecWarlock


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