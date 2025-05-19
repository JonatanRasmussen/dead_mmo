from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.id_gen import IdGen
from src.config.spell_db.templates.movement_spell_templates import MovementSpellTemplates


class MovementSpellCollection:
    @staticmethod
    def start_move_down() -> Spell:
        return MovementSpellTemplates.begin_movement(
            spell_id=271,
            aura_effect_id=MovementSpellCollection.step_down().spell_id
        )

    @staticmethod
    def stop_move_down() -> Spell:
        return MovementSpellTemplates.cancel_movement(
            spell_id=272,
            aura_effect_id=MovementSpellCollection.start_move_down().spell_id
        )

    @staticmethod
    def step_down() -> Spell:
        return MovementSpellTemplates.step_movement(
            spell_id=273,
            direction=SpellFlag.STEP_DOWN
        )

    @staticmethod
    def start_move_right() -> Spell:
        return MovementSpellTemplates.begin_movement(
            spell_id=1,
            aura_effect_id=MovementSpellCollection.step_right().spell_id
        )

    @staticmethod
    def stop_move_right() -> Spell:
        return MovementSpellTemplates.cancel_movement(
            spell_id=2,
            aura_effect_id=MovementSpellCollection.start_move_right().spell_id
        )

    @staticmethod
    def step_right() -> Spell:
        return MovementSpellTemplates.step_movement(
            spell_id=3,
            direction=SpellFlag.STEP_RIGHT
        )

    @staticmethod
    def start_move_up() -> Spell:
        return MovementSpellTemplates.begin_movement(
            spell_id=91,
            aura_effect_id=MovementSpellCollection.step_up().spell_id
        )

    @staticmethod
    def stop_move_up() -> Spell:
        return MovementSpellTemplates.cancel_movement(
            spell_id=92,
            aura_effect_id=MovementSpellCollection.start_move_up().spell_id
        )

    @staticmethod
    def step_up() -> Spell:
        return MovementSpellTemplates.step_movement(
            spell_id=93,
            direction=SpellFlag.STEP_UP
        )

    @staticmethod
    def start_move_left() -> Spell:
        return MovementSpellTemplates.begin_movement(
            spell_id=181,
            aura_effect_id=MovementSpellCollection.step_left().spell_id
        )

    @staticmethod
    def stop_move_left() -> Spell:
        return MovementSpellTemplates.cancel_movement(
            spell_id=182,
            aura_effect_id=MovementSpellCollection.start_move_left().spell_id
        )

    @staticmethod
    def step_left() -> Spell:
        return MovementSpellTemplates.step_movement(
            spell_id=183,
            direction=SpellFlag.STEP_LEFT
        )