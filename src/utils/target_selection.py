from typing import Dict, List, Tuple, ValuesView
import heapq

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import EventOutcome, CombatEvent, FinalizedEvent
from src.models.important_ids import ImportantIDs

class TargetSelection:

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
    def handle_aoe(source: GameObj, spell: Spell, target_id: GameObj, all_game_objs: ValuesView[GameObj]) -> List[int]:
        # not implemented
        if spell.flags & SpellFlag.TARGET_ALL:
            return []
        return [source.obj_id, target_id.obj_id, len(all_game_objs)]


    @staticmethod
    def handle_tab_targeting(target_obj: GameObj, important_ids: ImportantIDs) -> GameObj:
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