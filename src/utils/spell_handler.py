from typing import Dict, List, Tuple, ValuesView
import heapq

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import EventOutcome, CombatEvent, FinalizedEvent
from src.handlers.game_obj_handler import GameObjHandler

class SpellHandler:

    @staticmethod
    def select_target(source: GameObj, spell: Spell, target_id: int, all_game_objs: GameObjHandler) -> GameObj:
        if spell.flags & SpellFlag.SELF_CAST:
            return source
        if not IdGen.is_empty_id(target_id):
            return all_game_objs.get_game_obj(target_id)
        if spell.flags & SpellFlag.DAMAGE:
            if source.is_allied:
                return all_game_objs.get_game_obj(all_game_objs.boss1_id)
            return all_game_objs.get_game_obj(all_game_objs.player_id)
        if spell.flags & SpellFlag.HEAL:
            return source
        return source

    @staticmethod
    def modify_target(source_obj: GameObj, spell: Spell, target_obj: GameObj, delta_time: float, player_id: int, boss1_id: int, boss2_id: int) -> GameObj:
        tar = target_obj
        if spell.flags & SpellFlag.TAB_TARGET:
            tar = SpellHandler._handle_tab_targeting(tar, player_id, boss1_id, boss2_id)
        if spell.flags & (SpellFlag.MOVE_UP | SpellFlag.MOVE_LEFT | SpellFlag.MOVE_DOWN | SpellFlag.MOVE_RIGHT):
            tar = SpellHandler._handle_movement(spell, tar, delta_time)
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
    def _handle_tab_targeting(target_obj: GameObj, player_id: int, boss1_id: int, boss2_id: int) -> GameObj:
        if not target_obj.is_allied:
            return target_obj.switch_target(player_id)
        elif target_obj.current_target == boss1_id and IdGen.is_valid_id(boss2_id):
            return target_obj.switch_target(boss2_id)
        elif IdGen.is_valid_id(boss1_id):
            return target_obj.switch_target(boss1_id)
        else:
            # Not implemented. For now, let's assume boss1 always exist.
            assert False
            return target_obj.switch_target(player_id)

    @staticmethod
    def _handle_movement(spell: Spell, target_obj: GameObj, delta_time: float) -> GameObj:
        tar = target_obj
        if spell.flags & SpellFlag.MOVE_UP:
            tar = tar.move_in_direction(0.0, 1.0, tar.movement_speed, delta_time)
        if spell.flags & SpellFlag.MOVE_LEFT:
            tar = tar.move_in_direction(-1.0, 0.0, tar.movement_speed, delta_time)
        if spell.flags & SpellFlag.MOVE_DOWN:
            tar = tar.move_in_direction(0.0, -1.0, tar.movement_speed, delta_time)
        if spell.flags & SpellFlag.MOVE_RIGHT:
            tar = tar.move_in_direction(1.0, 0.0, tar.movement_speed, delta_time)
        return tar