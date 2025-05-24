from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.spell_templates import SpellTemplates


class MovementSpellCollection:

    @staticmethod
    def start_move_up() -> Spell:
        return SpellTemplates.begin_movement(
            spell_id=91,
            direction=SpellFlag.STEP_UP,
        )

    @staticmethod
    def stop_move_up() -> Spell:
        return SpellTemplates.cancel_movement(
            spell_id=92,
            referenced_spell=MovementSpellCollection.start_move_up().spell_id
        )

    @staticmethod
    def start_move_left() -> Spell:
        return SpellTemplates.begin_movement(
            spell_id=181,
            direction=SpellFlag.STEP_LEFT,
        )

    @staticmethod
    def stop_move_left() -> Spell:
        return SpellTemplates.cancel_movement(
            spell_id=182,
            referenced_spell=MovementSpellCollection.start_move_left().spell_id
        )

    @staticmethod
    def start_move_down() -> Spell:
        return SpellTemplates.begin_movement(
            spell_id=271,
            direction=SpellFlag.STEP_DOWN,
        )

    @staticmethod
    def stop_move_down() -> Spell:
        return SpellTemplates.cancel_movement(
            spell_id=272,
            referenced_spell=MovementSpellCollection.start_move_down().spell_id
        )

    @staticmethod
    def start_move_right() -> Spell:
        return SpellTemplates.begin_movement(
            spell_id=1,
            direction=SpellFlag.STEP_RIGHT,
        )

    @staticmethod
    def stop_move_right() -> Spell:
        return SpellTemplates.cancel_movement(
            spell_id=2,
            referenced_spell=MovementSpellCollection.start_move_right().spell_id
        )