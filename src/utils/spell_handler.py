from typing import Dict, List, Tuple, ValuesView
import heapq

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import EventOutcome, CombatEvent, FinalizedEvent
from src.models.important_ids import ImportantIDs
from src.handlers.game_obj_handler import GameObjHandler

class SpellHandler:

    @staticmethod
    def select_target(source: GameObj, spell: Spell, target_id: int, important_ids: ImportantIDs) -> int:
        if spell.flags & SpellFlag.SELF_CAST:
            return source.obj_id
        if not IdGen.is_empty_id(target_id):
            return target_id
        if spell.flags & SpellFlag.DAMAGE:
            if source.is_allied:
                return important_ids.boss1_id
            return important_ids.player_id
        if spell.flags & SpellFlag.HEAL:
            return source.obj_id
        return source.obj_id

    @staticmethod
    def modify_target(source_obj: GameObj, spell: Spell, target_obj: GameObj, important_ids: ImportantIDs) -> GameObj:
        tar = target_obj
        if spell.flags & SpellFlag.TAB_TARGET:
            tar = SpellHandler._handle_tab_targeting(tar, important_ids)
        if spell.flags & (SpellFlag.STEP_UP | SpellFlag.STEP_LEFT | SpellFlag.STEP_DOWN | SpellFlag.STEP_RIGHT):
            tar = SpellHandler._handle_movement(spell, tar)
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
    def _handle_tab_targeting(target_obj: GameObj, important_ids: ImportantIDs) -> GameObj:
        if not target_obj.is_allied:
            return target_obj.switch_target(important_ids.player_id)
        elif target_obj.current_target == important_ids.boss1_id and important_ids.boss2_exists:
            return target_obj.switch_target(important_ids.boss2_id)
        elif IdGen.is_valid_id(important_ids.boss1_id):
            return target_obj.switch_target(important_ids.boss1_id)
        else:
            # Not implemented. For now, let's assume boss1 always exist.
            assert False
            return target_obj.switch_target(important_ids.player_id)

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