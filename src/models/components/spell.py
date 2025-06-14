from typing import List, Tuple, Optional, NamedTuple, ValuesView
from enum import Enum, Flag, auto
from src.config import Consts
from .important_ids import ImportantIDs
from .game_obj import GameObj, GameObjStatus, Controls


class SpellFlag(Flag):
    """ Various Spell boolians """
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
        """SpellFlag.AURA_CANCEL in self.flags"""
        tar = target_obj
        if self & (SpellFlag.STEP_UP | SpellFlag.STEP_LEFT | SpellFlag.STEP_DOWN | SpellFlag.STEP_RIGHT):
            tar = self._handle_movement(tar)
        if self & (SpellFlag.SET_ABILITY_SLOT_1 | SpellFlag.SET_ABILITY_SLOT_2 | SpellFlag.SET_ABILITY_SLOT_3 | SpellFlag.SET_ABILITY_SLOT_4):
            tar = self._handle_ability_swaps(referenced_spell, tar)
        if self & SpellFlag.DAMAGING:
            tar = tar.suffer_damage(power * source_obj.spell_modifier)
        if self & SpellFlag.HEALING:
            tar = tar.restore_health(power * source_obj.spell_modifier)
        return tar

    def modify_source(self, timestamp: float, source_obj: GameObj, target_obj: GameObj) -> GameObj:
        src = source_obj
        if self & SpellFlag.UPDATE_CURRENT_TARGET:
            src = src.switch_target(target_obj.obj_id)
        if self & SpellFlag.TRIGGER_GCD:
            src = src.set_gcd_start(timestamp)
        if self & SpellFlag.DESPAWN_SELF:
            src = src.change_status(GameObjStatus.DESPAWNED)
        if self & SpellFlag.MOVE_TOWARDS_TARGET:
            src = src.move_towards_coordinates(target_obj.x, target_obj.y, src.movement_speed * 0.0005)
        if self & SpellFlag.TELEPORT_TO_TARGET:
            src = src.teleport_to_coordinates(target_obj.x, target_obj.y)
        return src

    def _handle_movement(self, target_obj: GameObj) -> GameObj:
        BASE_MOVE_DISTANCE = 0.001
        tar = target_obj
        if self & SpellFlag.STEP_UP:
            tar = tar.move_in_direction(0.0, 1.0, tar.movement_speed * BASE_MOVE_DISTANCE)
        if self & SpellFlag.STEP_LEFT:
            tar = tar.move_in_direction(-1.0, 0.0, tar.movement_speed * BASE_MOVE_DISTANCE)
        if self & SpellFlag.STEP_DOWN:
            tar = tar.move_in_direction(0.0, -1.0, tar.movement_speed * BASE_MOVE_DISTANCE)
        if self & SpellFlag.STEP_RIGHT:
            tar = tar.move_in_direction(1.0, 0.0, tar.movement_speed * BASE_MOVE_DISTANCE)
        return tar

    def _handle_ability_swaps(self, referenced_spell: int, target_obj: GameObj) -> GameObj:
        tar = target_obj
        if self & SpellFlag.SET_ABILITY_SLOT_1:
            tar = tar.set_ability_1(referenced_spell)
        if self & SpellFlag.SET_ABILITY_SLOT_2:
            tar = tar.set_ability_2(referenced_spell)
        if self & SpellFlag.SET_ABILITY_SLOT_3:
            tar = tar.set_ability_3(referenced_spell)
        if self & SpellFlag.SET_ABILITY_SLOT_4:
            tar = tar.set_ability_4(referenced_spell)
        return tar


class SpellTarget(Enum):
    """ Defines targeting behavior for spell """
    NONE = 0
    SELF = auto()
    PARENT = auto()
    AURA_TARGET = auto()
    CURRENT_TARGET = auto()
    DEFAULT_FRIENDLY = auto()
    DEFAULT_ENEMY = auto()
    TAB_TO_NEXT = auto()

    @property
    def is_target_swap(self) -> bool:
        return self in {SpellTarget.TAB_TO_NEXT}

    def select_target(self, source: GameObj, aura_target: int, important_ids: ImportantIDs) -> int:
        assert self not in {SpellTarget.NONE}, f"obj {source.obj_id} is casting a spell with targeting=NONE"
        if self in {SpellTarget.SELF}:
            return source.obj_id
        if self in {SpellTarget.AURA_TARGET} and Consts.is_valid_id(aura_target):
            return aura_target
        if self in {SpellTarget.CURRENT_TARGET} and Consts.is_valid_id(aura_target):
            return source.current_target
        if self in {SpellTarget.PARENT} and Consts.is_valid_id(source.parent_id):
            return source.parent_id
        if self in {SpellTarget.DEFAULT_ENEMY}:
            if source.is_allied:
                return important_ids.boss1_id
            return important_ids.player_id
        if self in {SpellTarget.DEFAULT_FRIENDLY}:
            return source.obj_id
        if self.is_target_swap:
            if self in {SpellTarget.TAB_TO_NEXT}:
                if not source.is_allied:
                    return important_ids.player_id
                elif source.current_target == important_ids.boss1_id and important_ids.boss2_exists:
                    return important_ids.boss2_id
                elif Consts.is_valid_id(important_ids.boss1_id):
                    return important_ids.boss1_id
                else:
                    # Not implemented. For now, let's assume boss1 always exist.
                    return important_ids.player_id
        return important_ids.missing_target_id

    @staticmethod
    def handle_aoe(source: GameObj, target_id: GameObj, all_game_objs: ValuesView[GameObj]) -> List[int]:
        # not implemented
        return [source.obj_id, target_id.obj_id, len(all_game_objs)]


class Spell(NamedTuple):
    """ An action that can be performed by a game object. """
    spell_id: int = Consts.EMPTY_ID
    alias_id: int = Consts.EMPTY_ID

    power: float = 1.0
    variance: float = 0.0

    range_limit: float = 0.0
    #self.cost: float = 0 #not yet implemented
    #self.gcd_mod: float = 0.0 #not yet implemented
    cast_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    max_stacks: int = 1

    flags: SpellFlag = SpellFlag.NONE
    targeting: SpellTarget = SpellTarget.NONE

    external_spell: int = Consts.EMPTY_ID
    spell_sequence: Optional[Tuple[int, ...]] = None
    spawned_obj: Optional['GameObj'] = None
    obj_controls: Optional[Tuple[Controls, ...]] = None

    # Audio properties
    audio_name: str = ""
    spell_type: str = ""

    # Animation properties
    animation_name: str = ""
    animation_scale: float = 1.0

    # Effect placement
    animate_on_target: bool = True  # If False, animate on source

    @property
    def should_play_audio(self) -> bool:
        return self.audio_name is not None and self.audio_name != ""
    @property
    def should_play_animation(self) -> bool:
        return self.animation_name is not None and self.animation_name != ""

    @property
    def is_modifying_source(self) -> bool:
        return True  # While I'm still frequently adding new flags, just return True
        # return bool(self.flags & SpellFlag.TRIGGER_GCD)

    @property
    def has_range_limit(self) -> bool:
        return self.range_limit > 0.0

    @property
    def has_aura_apply(self) -> bool:
        return SpellFlag.AURA_APPLY in self.flags

    @property
    def has_aura_cancel(self) -> bool:
        return SpellFlag.AURA_CANCEL in self.flags

    @property
    def has_cascading_events(self) -> bool:
        return (
            self.is_area_of_effect or
            self.has_aura_apply or
            self.spawned_obj is not None or
            self.spell_sequence is not None
        )

    #Targeting

    @property
    def is_target_of_target(self) -> bool:
        return SpellFlag.TARGET_OF_TARGET in self.flags

    @property
    def is_area_of_effect(self) -> bool:
        return SpellFlag.AOE in self.flags
