from typing import Dict, List, Tuple, ValuesView
import heapq

from src.models.world_state import WorldState
from src.models.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.combat_event import EventOutcome, CombatEvent
from src.config.spell_db import SpellDatabase


class SpellHandler:

    @staticmethod
    def handle_spell(source_obj: GameObj, spell: Spell, target_obj: GameObj, state: WorldState) -> None:
        if spell.spawned_obj is not None:
            SpellHandler._handle_spawn(source_obj, spell, state)
        if spell.flags & SpellFlag.AURA:
            state.add_aura(source_obj.obj_id, spell, target_obj.obj_id)
        updated_source_obj = SpellHandler._modify_source(source_obj, spell, state)
        state.update_game_obj(updated_source_obj)
        updated_target_obj = SpellHandler._modify_target(updated_source_obj, spell, target_obj, state)
        state.update_game_obj(updated_target_obj)

    @staticmethod
    def select_target(event: CombatEvent, source: GameObj, spell: Spell, state: WorldState) -> GameObj:
        if spell.flags & SpellFlag.SELF_CAST:
            return source
        if not IdGen.is_empty_id(event.target):
            return state.get_game_obj(event.target)
        if spell.flags & SpellFlag.DAMAGE:
            if source.is_allied:
                return state.get_game_obj(state.boss1_id)
            return state.get_game_obj(state.player_id)
        if spell.flags & SpellFlag.HEAL:
            return source
        return source

    @staticmethod
    def _modify_target(source_obj: GameObj, spell: Spell, target_obj: GameObj, state: WorldState) -> GameObj:
        tar = target_obj
        if spell.flags & SpellFlag.TAB_TARGET:
            tar = SpellHandler._handle_tab_targeting(target_obj, state)
        if spell.flags & (SpellFlag.MOVE_UP | SpellFlag.MOVE_LEFT | SpellFlag.MOVE_DOWN | SpellFlag.MOVE_RIGHT):
            tar = SpellHandler._handle_movement(spell, tar, state)
        if spell.flags & SpellFlag.DAMAGE:
            tar = tar.suffer_damage(spell.power * source_obj.spell_modifier)
        if spell.flags & SpellFlag.HEAL:
            tar = tar.restore_health(spell.power * source_obj.spell_modifier)
        return tar

    @staticmethod
    def _modify_source(source_obj: GameObj, spell: Spell, state: WorldState) -> GameObj:
        src = source_obj
        if spell.flags & SpellFlag.TRIGGER_GCD:
            src = src.set_gcd_start(state.current_timestamp)
        return src

    @staticmethod
    def _handle_movement(spell: Spell, target_obj: GameObj, state: WorldState) -> GameObj:
        tar = target_obj
        if spell.flags & SpellFlag.MOVE_UP:
            tar = target_obj.move_in_direction(0.0, 1.0, target_obj.movement_speed, state.delta_time)
        if spell.flags & SpellFlag.MOVE_LEFT:
            tar = target_obj.move_in_direction(-1.0, 0.0, target_obj.movement_speed, state.delta_time)
        if spell.flags & SpellFlag.MOVE_DOWN:
            tar = target_obj.move_in_direction(0.0, -1.0, target_obj.movement_speed, state.delta_time)
        if spell.flags & SpellFlag.MOVE_RIGHT:
            tar = target_obj.move_in_direction(1.0, 0.0, target_obj.movement_speed, state.delta_time)
        return tar

    @staticmethod
    def _handle_spawn(source_obj: GameObj, spell: Spell, state: WorldState) -> None:
        if spell.spawned_obj is not None:
            obj_id = state.game_obj_id_gen.new_id()
            new_obj = GameObj.create_from_template(obj_id, source_obj.obj_id, spell.spawned_obj)
            state.add_game_obj(new_obj)
            if spell.obj_controls is not None:
                for controls in spell.obj_controls:
                    state.add_controls(obj_id, controls.timestamp, controls)
        if spell.flags & SpellFlag.SPAWN_BOSS:
            if not state.boss1_exists:
                state.boss1_id = new_obj.obj_id
            else:
                assert not state.boss2_exists, "Second boss already exists."
                state.boss2_id = new_obj.obj_id
        if spell.flags & SpellFlag.SPAWN_PLAYER:
            assert not state.player_exists, "Player already exists."
            state.player_id = new_obj.obj_id

    @staticmethod
    def _handle_tab_targeting(target_obj: GameObj, state: WorldState) -> GameObj:
        if not target_obj.is_allied:
            return target_obj.switch_target(state.player_id)
        elif target_obj.current_target == state.boss1_id and state.boss2_exists:
            return target_obj.switch_target(state.boss2_id)
        elif state.boss1_exists:
            return target_obj.switch_target(state.boss1_id)
        else:
            # Not implemented. For now, let's assume boss1 always exist.
            assert False
            return target_obj.switch_target(state.player_id)
