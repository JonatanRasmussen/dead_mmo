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
    def new_player(spell_id: int, hp: float, x: float, y: float, color: Tuple[int, int, int]) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_PLAYER | SpellFlag.SELF_CAST,
            spawned_obj=GameObj(
                spawned_from_spell=spell_id,
                hp=hp,
                is_allied=True,
                x=x,
                y=y,
                color=color,
                start_move_up_id=MovementSpellCollection.start_move_up().spell_id,
                stop_move_up_id=MovementSpellCollection.stop_move_up().spell_id,
                start_move_left_id=MovementSpellCollection.start_move_left().spell_id,
                stop_move_left_id=MovementSpellCollection.stop_move_left().spell_id,
                start_move_down_id=MovementSpellCollection.start_move_down().spell_id,
                stop_move_down_id=MovementSpellCollection.stop_move_down().spell_id,
                start_move_right_id=MovementSpellCollection.start_move_right().spell_id,
                stop_move_right_id=MovementSpellCollection.stop_move_right().spell_id,
                next_target_id=UniqueSpellCollection.tab_target().spell_id,
                ability_1_id=CombatSpellCollection.fireblast().spell_id,
                ability_2_id=CombatSpellCollection.fireblast().spell_id,
                ability_3_id=CombatSpellCollection.fireblast().spell_id,
                ability_4_id=CombatSpellCollection.fireblast().spell_id,
            ),
        )

    @staticmethod
    def new_boss(spell_id: int, hp: float, x: float, y: float, color: Tuple[int, int, int], obj_controls: Optional[Tuple[Controls, ...]]) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
            spawned_obj=GameObj(
                spawned_from_spell=spell_id,
                hp=hp,
                x=x,
                y=y,
                color=color,
                ability_1_id=CombatSpellCollection.small_heal().spell_id,
                ability_2_id=CombatSpellCollection.healing_aura().spell_id,
                ability_3_id=CombatSpellCollection.fireblast().spell_id,
            ),
            obj_controls=obj_controls
        )