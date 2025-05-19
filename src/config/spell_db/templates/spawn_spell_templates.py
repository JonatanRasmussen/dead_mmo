from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.collections.movement_spell_collection import MovementSpellCollection
from src.config.spell_db.collections.combat_spell_collection import CombatSpellCollection
from src.config.spell_db.collections.unique_spell_collection import UniqueSpellCollection


class SpawnSpellTemplates:
    @staticmethod
    def new_player(spell_id: int, spawned_obj: GameObj) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_PLAYER | SpellFlag.SELF_CAST,
            spawned_obj=spawned_obj._replace(
                spawned_from_spell=spell_id,
                is_allied=True,
            ),
        )

    @staticmethod
    def new_boss(spell_id: int, spawned_obj: GameObj, obj_controls: Optional[Tuple[Controls, ...]],) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
            spawned_obj=spawned_obj._replace(
                spawned_from_spell=spell_id,
            ),
            obj_controls=obj_controls
        )

    @staticmethod
    def new_hitbox(spell_id: int, spawned_obj: GameObj, obj_controls: Optional[Tuple[Controls, ...]],) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SELF_CAST,
            spawned_obj=spawned_obj._replace(
                spawned_from_spell=spell_id,
            ),
            obj_controls=obj_controls
        )