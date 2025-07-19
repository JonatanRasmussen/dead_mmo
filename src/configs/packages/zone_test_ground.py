from src.settings import AudioFiles, Colors, Consts
from src.models.components import Controls, GameObj, Faction, Loadout, Position, Resources
from src.models.data import Behavior, Targeting, Spell
from src.configs.blueprints import SpellFactory, SpellTemplates, GameObjFactory, GameObjTemplates
from .spec_warlock import SpecWarlock
from .npc_boss import NpcBoss
from .npc_target_dummy import NpcTargetDummy
from .npc_landmine import NpcLandmine


class ZoneTestGround:
    @staticmethod
    def setup_test_zone() -> SpellFactory:
        spell_sequence = (
            NpcBoss.spawn_boss().spell_id,
            SpecWarlock.spawn_player().spell_id,
        )
        return (
            SpellFactory(300)
            .cast_on_self()
            .set_spell_sequence(spell_sequence)
        )
