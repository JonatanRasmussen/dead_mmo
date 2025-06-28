from typing import List, Tuple, Iterable, NamedTuple, Optional, ValuesView
from enum import Enum, Flag, auto

from .game_obj import GameObj
from .obj_status import ObjStatus


class Behavior(Flag):
    """ Various bitflags that define spell behavior. """
    NONE = 0
    STEP_UP = auto()
    STEP_LEFT = auto()
    STEP_DOWN = auto()
    STEP_RIGHT = auto()
    MOVE_TOWARDS_TARGET = auto()
    TELEPORT_TO_TARGET = auto()
    SET_ABILITY_SLOT_1 = auto()
    SET_ABILITY_SLOT_2 = auto()
    SET_ABILITY_SLOT_3 = auto()
    SET_ABILITY_SLOT_4 = auto()
    TRIGGER_GCD = auto()
    DAMAGING = auto()
    HEALING = auto()
    AOE = auto()
    TARGET_OF_TARGET = auto()
    DENY_IF_CASTING = auto()
    IS_CHANNEL = auto()
    TRY_MOVE = auto()
    FORCE_MOVE = auto()
    UPDATE_CURRENT_TARGET = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    AURA_APPLY = auto()
    AURA_CANCEL = auto()

    def modify_target(self, source_obj: GameObj, power: float, referenced_spell: int, target_obj: GameObj) -> GameObj:
        tar = target_obj
        if self & (Behavior.STEP_UP | Behavior.STEP_LEFT | Behavior.STEP_DOWN | Behavior.STEP_RIGHT):
            tar = self._handle_movement(tar)
        if self & (Behavior.SET_ABILITY_SLOT_1 | Behavior.SET_ABILITY_SLOT_2 | Behavior.SET_ABILITY_SLOT_3 | Behavior.SET_ABILITY_SLOT_4):
            tar = self._handle_ability_swaps(referenced_spell, tar)
        if self & Behavior.DAMAGING:
            tar = tar.suffer_damage(power * source_obj.spell_modifier)
        if self & Behavior.HEALING:
            tar = tar.restore_health(power * source_obj.spell_modifier)
        return tar

    def modify_source(self, timestamp: float, source_obj: GameObj, target_obj: GameObj) -> GameObj:
        src = source_obj
        if self & Behavior.UPDATE_CURRENT_TARGET:
            src = src.switch_target(target_obj.obj_id)
        if self & Behavior.TRIGGER_GCD:
            src = src.set_gcd_start(timestamp)
        if self & Behavior.DESPAWN_SELF:
            src = src.change_status(ObjStatus.DESPAWNED)
        if self & Behavior.MOVE_TOWARDS_TARGET:
            src = src.move_towards_coordinates(target_obj.x, target_obj.y, src.movement_speed)
        if self & Behavior.TELEPORT_TO_TARGET:
            src = src.teleport_to_coordinates(target_obj.x, target_obj.y)
        return src

    def _handle_movement(self, target_obj: GameObj) -> GameObj:
        tar = target_obj
        if self & Behavior.STEP_UP:
            tar = tar.move_in_direction(0.0, 1.0, tar.movement_speed)
        if self & Behavior.STEP_LEFT:
            tar = tar.move_in_direction(-1.0, 0.0, tar.movement_speed)
        if self & Behavior.STEP_DOWN:
            tar = tar.move_in_direction(0.0, -1.0, tar.movement_speed)
        if self & Behavior.STEP_RIGHT:
            tar = tar.move_in_direction(1.0, 0.0, tar.movement_speed)
        return tar

    def _handle_ability_swaps(self, referenced_spell: int, target_obj: GameObj) -> GameObj:
        tar = target_obj
        if self & Behavior.SET_ABILITY_SLOT_1:
            tar = tar.set_ability_1(referenced_spell)
        if self & Behavior.SET_ABILITY_SLOT_2:
            tar = tar.set_ability_2(referenced_spell)
        if self & Behavior.SET_ABILITY_SLOT_3:
            tar = tar.set_ability_3(referenced_spell)
        if self & Behavior.SET_ABILITY_SLOT_4:
            tar = tar.set_ability_4(referenced_spell)
        return tar