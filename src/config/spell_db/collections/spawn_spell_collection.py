from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.spawn_spell_templates import SpawnSpellTemplates
from src.config.spell_db.collections.movement_spell_collection import MovementSpellCollection
from src.config.spell_db.collections.combat_spell_collection import CombatSpellCollection
from src.config.spell_db.collections.unique_spell_collection import UniqueSpellCollection


class SpawnSpellCollection:
    @staticmethod
    def spawn_single_step_player() -> Spell:
        spell_id = 199
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_PLAYER | SpellFlag.SELF_CAST,
            spawned_obj=GameObj(
                spawned_from_spell=spell_id,
                hp=30.0,
                is_allied=True,
                x=0.3,
                y=0.3,
                color=Color.RED,
                start_move_up_id=MovementSpellCollection.step_up().spell_id,
                stop_move_up_id=MovementSpellCollection.step_up().spell_id,
                start_move_left_id=MovementSpellCollection.step_left().spell_id,
                stop_move_left_id=MovementSpellCollection.step_left().spell_id,
                start_move_down_id=MovementSpellCollection.step_down().spell_id,
                stop_move_down_id=MovementSpellCollection.step_down().spell_id,
                start_move_right_id=MovementSpellCollection.step_right().spell_id,
                stop_move_right_id=MovementSpellCollection.step_right().spell_id,
                next_target_id=UniqueSpellCollection.tab_target().spell_id,
                ability_1_id=CombatSpellCollection.fireblast().spell_id,
                ability_2_id=CombatSpellCollection.fireblast().spell_id,
                ability_3_id=CombatSpellCollection.fireblast().spell_id,
                ability_4_id=CombatSpellCollection.fireblast().spell_id,
            ),
        )

    @staticmethod
    def spawn_player() -> Spell:
        return SpawnSpellTemplates.new_player(
            spell_id=200,
            hp=30.0,
            x=0.3,
            y=0.3,
            color=Color.RED,
        )

    @staticmethod
    def spawn_enemy() -> Spell:
        return SpawnSpellTemplates.new_boss(
            spell_id=201,
            hp=30.0,
            x=0.7,
            y=0.7,
            color=Color.GREEN,
            obj_controls=(
                Controls(timestamp=3.0, ability_1=True),
                Controls(timestamp=5.0, ability_2=True),
            )
        )

    @staticmethod
    def spawn_target_dummy() -> Spell:
        return SpawnSpellTemplates.new_boss(
            spell_id=202,
            hp=80.0,
            x=0.5,
            y=0.8,
            color=Color.BLUE,
            obj_controls=(
                Controls(timestamp=4.0, ability_3=True),
            )
        )