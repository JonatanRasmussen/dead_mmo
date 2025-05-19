from typing import Dict, List, Tuple, ValuesView
import heapq

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import EventOutcome, CombatEvent, FinalizedEvent
from src.models.important_ids import ImportantIDs
from src.utils.target_selection import TargetSelection

class SpellResolving:

    @staticmethod
    def modify_target(source_obj: GameObj, spell: Spell, target_obj: GameObj, important_ids: ImportantIDs) -> GameObj:
        tar = target_obj
        if spell.flags & SpellFlag.TAB_TARGET:
            tar = TargetSelection.handle_tab_targeting(tar, important_ids)
        if spell.flags & (SpellFlag.STEP_UP | SpellFlag.STEP_LEFT | SpellFlag.STEP_DOWN | SpellFlag.STEP_RIGHT):
            tar = SpellResolving._handle_movement(spell, tar)
        if spell.flags & (SpellFlag.SET_ABILITY_SLOT_1 | SpellFlag.SET_ABILITY_SLOT_2 | SpellFlag.SET_ABILITY_SLOT_3 | SpellFlag.SET_ABILITY_SLOT_4):
            tar = SpellResolving._handle_ability_swaps(spell, tar)
        if spell.flags & SpellFlag.DAMAGE:
            tar = tar.suffer_damage(spell.power * source_obj.spell_modifier)
        if spell.flags & SpellFlag.HEAL:
            tar = tar.restore_health(spell.power * source_obj.spell_modifier)
        return tar

    @staticmethod
    def modify_source(timestamp: float, source_obj: GameObj, spell: Spell) -> GameObj:
        src = source_obj
        if spell.flags & SpellFlag.TRIGGER_GCD:
            src = src.set_gcd_start(timestamp)
        return src

    @staticmethod
    def _handle_movement(spell: Spell, target_obj: GameObj) -> GameObj:
        BASE_MOVE_DISTANCE = 0.001
        tar = target_obj
        if spell.flags & SpellFlag.STEP_UP:
            tar = tar.move_in_direction(0.0, 1.0, tar.movement_speed, BASE_MOVE_DISTANCE)
        if spell.flags & SpellFlag.STEP_LEFT:
            tar = tar.move_in_direction(-1.0, 0.0, tar.movement_speed, BASE_MOVE_DISTANCE)
        if spell.flags & SpellFlag.STEP_DOWN:
            tar = tar.move_in_direction(0.0, -1.0, tar.movement_speed, BASE_MOVE_DISTANCE)
        if spell.flags & SpellFlag.STEP_RIGHT:
            tar = tar.move_in_direction(1.0, 0.0, tar.movement_speed, BASE_MOVE_DISTANCE)
        return tar

    @staticmethod
    def _handle_ability_swaps(spell: Spell, target_obj: GameObj) -> GameObj:
        tar = target_obj
        if spell.flags & SpellFlag.SET_ABILITY_SLOT_1:
            tar = tar.set_ability_1(spell.effect_id)
        if spell.flags & SpellFlag.SET_ABILITY_SLOT_2:
            tar = tar.set_ability_2(spell.effect_id)
        if spell.flags & SpellFlag.SET_ABILITY_SLOT_3:
            tar = tar.set_ability_3(spell.effect_id)
        if spell.flags & SpellFlag.SET_ABILITY_SLOT_4:
            tar = tar.set_ability_4(spell.effect_id)
        return tar