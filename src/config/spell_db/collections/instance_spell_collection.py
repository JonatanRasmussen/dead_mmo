from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.instance_spell_template import InstanceSpellTemplates
from src.config.spell_db.collections.spawn_spell_collection import SpawnSpellCollection


class InstanceSpellCollection:
    @staticmethod
    def setup_test_zone() -> Spell:
        return InstanceSpellTemplates.instance_setup(
            spell_id=300,
            spell_sequence=(
                SpawnSpellCollection.spawn_enemy().spell_id,
                SpawnSpellCollection.spawn_target_dummy().spell_id,
                SpawnSpellCollection.spawn_player().spell_id,
            ),
        )