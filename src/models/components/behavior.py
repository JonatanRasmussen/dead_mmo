from enum import Flag, auto

from .game_obj import GameObj
from .obj_status import ObjStatus
from .position import Position


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

    def modify_target(self, source_obj: GameObj, power: float, referenced_spell: int, target_obj: GameObj) -> None:
        if self & (Behavior.STEP_UP | Behavior.STEP_LEFT | Behavior.STEP_DOWN | Behavior.STEP_RIGHT):
            self._handle_movement(target_obj)
        if self & (Behavior.SET_ABILITY_SLOT_1 | Behavior.SET_ABILITY_SLOT_2 | Behavior.SET_ABILITY_SLOT_3 | Behavior.SET_ABILITY_SLOT_4):
            self._handle_ability_swaps(referenced_spell, target_obj)
        if self & Behavior.DAMAGING:
            target_obj.res.hp -= power * source_obj.spell_modifier
        if self & Behavior.HEALING:
            target_obj.res.hp += power * source_obj.spell_modifier

    def modify_source(self, timestamp: int, source_obj: GameObj, target_obj: GameObj) -> None:
        src = source_obj
        if self & Behavior.UPDATE_CURRENT_TARGET:
            source_obj.current_target = target_obj.obj_id
        if self & Behavior.TRIGGER_GCD:
            source_obj.cds.gcd_start = timestamp
        if self & Behavior.DESPAWN_SELF:
            source_obj.status = ObjStatus.DESPAWNED
        if self & Behavior.MOVE_TOWARDS_TARGET:
            source_obj.pos.move_towards_destination(target_obj.pos, src.mods.movement_speed)
        if self & Behavior.TELEPORT_TO_TARGET:
            source_obj.pos.teleport_to_position(target_obj.pos)

    def _handle_movement(self, target_obj: GameObj) -> None:
        if self & Behavior.STEP_UP:
            target_obj.pos.move_in_direction(Position(x=0.0, y=1.0), target_obj.mods.movement_speed)
        if self & Behavior.STEP_LEFT:
            target_obj.pos.move_in_direction(Position(x=-1.0, y=0.0), target_obj.mods.movement_speed)
        if self & Behavior.STEP_DOWN:
            target_obj.pos.move_in_direction(Position(x=0.0, y=-1.0), target_obj.mods.movement_speed)
        if self & Behavior.STEP_RIGHT:
            target_obj.pos.move_in_direction(Position(x=1.0, y=0.0), target_obj.mods.movement_speed)

    def _handle_ability_swaps(self, referenced_spell: int, target_obj: GameObj) -> None:
        if self & Behavior.SET_ABILITY_SLOT_1:
            target_obj.loadout.ability_1_id = referenced_spell
        if self & Behavior.SET_ABILITY_SLOT_2:
            target_obj.loadout.ability_2_id = referenced_spell
        if self & Behavior.SET_ABILITY_SLOT_3:
            target_obj.loadout.ability_3_id = referenced_spell
        if self & Behavior.SET_ABILITY_SLOT_4:
            target_obj.loadout.ability_4_id = referenced_spell