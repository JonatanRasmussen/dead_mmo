from src.config import AudioFiles, Colors, Consts
from src.models import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.handlers.spell_factory import SpellFactory, SpellTemplates
from src.templates.spec_warlock import SpecWarlock
from src.templates.npc_boss import NpcBoss
from src.templates.npc_target_dummy import NpcTargetDummy
from src.templates.npc_landmine import NpcLandmine


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
