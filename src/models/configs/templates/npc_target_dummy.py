from src.config import AudioFiles, Colors, Consts
from src.models.components import Controls, Distance, GameObj, Faction, KeyPresses, Loadout, Position, Resources
from src.models.configs import Behavior, Targeting, Spell
from src.models.services import SpellFactory, SpellTemplates, GameObjFactory, GameObjTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting
from .spec_warlock import SpecWarlock


class NpcTargetDummy:
    @staticmethod
    def spawn_target_dummy() -> SpellFactory:
        timeline = {
            1500: BasicTargeting.targetswap_to_next_tab_target().spell_id,
            4000: SpecWarlock.fire_blast().spell_id,
            7000: BasicMovement.start_move_towards_target().spell_id,
        }
        obj_template = GameObjTemplates.create_enemy(timeline, x=-0.2, y=0.1, hp=80.0, color=Colors.BLUE)
        return (
            SpellFactory(70)
            .spawn_boss(obj_template)
        )