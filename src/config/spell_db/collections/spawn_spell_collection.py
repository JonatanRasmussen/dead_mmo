from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.spell_templates import SpellTemplates
from src.config.spell_db.collections.unique_spell_collection import UniqueSpellCollection
from src.config.spell_db.collections.combat_spell_collection import CombatSpellCollection
from src.config.spell_db.collections.movement_spell_collection import MovementSpellCollection


class SpawnSpellCollection:
    @staticmethod
    def spawn_player() -> Spell:
        return SpellTemplates.new_player(
            spell_id=200,
            spawned_obj=GameObj(
                hp=30.0,
                x=0.3,
                y=0.3,
                color=Color.RED,
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
    def spawn_enemy() -> Spell:
        return SpellTemplates.new_boss(
            spell_id=201,
            spawned_obj=GameObj(
                hp=30.0,
                x=0.7,
                y=0.7,
                color=Color.GREEN,
                next_target_id=UniqueSpellCollection.tab_target().spell_id,
                ability_1_id=CombatSpellCollection.small_heal().spell_id,
                ability_2_id=CombatSpellCollection.healing_aura().spell_id,
            ),
            obj_controls=(
                Controls(timestamp=1.0, next_target=True),
                Controls(timestamp=3.0, ability_1=True),
                Controls(timestamp=5.0, ability_2=True),
            ),
        )

    @staticmethod
    def spawn_target_dummy() -> Spell:
        return SpellTemplates.new_boss(
            spell_id=202,
            spawned_obj=GameObj(
                hp=80.0,
                x=0.5,
                y=0.8,
                color=Color.BLUE,
                next_target_id=UniqueSpellCollection.tab_target().spell_id,
                ability_3_id=CombatSpellCollection.fireblast().spell_id,
                ability_4_id=CombatSpellCollection.short_range_hurtbox().spell_id,
            ),
            obj_controls=(
                Controls(timestamp=1.0, next_target=True),
                Controls(timestamp=4.0, ability_3=True),
                Controls(timestamp=7.0, ability_4=True),
            ),
        )

    @staticmethod
    def spawn_landmine() -> Spell:
        return SpellTemplates.new_hitbox(
            spell_id=203,
            spawned_obj=GameObj(
                hp=20.0,
                x=0.2,
                y=0.8,
                color=Color.MAGENTA,
                ability_1_id=CombatSpellCollection.landmine_aura().spell_id,
            ),
            obj_controls=(
                Controls(timestamp=1.5, ability_1=True),
            ),
        )