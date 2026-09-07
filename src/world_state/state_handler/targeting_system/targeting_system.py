from dataclasses import dataclass
from typing import Dict, Iterable
from src.settings import Consts
from src.world_state.state_handler._spell_loader import Effect

@dataclass(slots=True)
class DefaultIDs:
    environment_id: int = Consts.EMPTY_ID
    player_id: int = Consts.EMPTY_ID
    boss1_id: int = Consts.EMPTY_ID
    boss2_id: int = Consts.EMPTY_ID

    @property
    def environment_exists(self) -> bool: return Consts.is_valid_id(self.environment_id)
    @property
    def player_exists(self) -> bool: return Consts.is_valid_id(self.player_id)
    @property
    def boss1_exists(self) -> bool: return Consts.is_valid_id(self.boss1_id)
    @property
    def boss2_exists(self) -> bool: return Consts.is_valid_id(self.boss2_id)

@dataclass(slots=True)
class ObjTargetingData:
    parent_id: int = Consts.EMPTY_ID
    current_target_id: int = Consts.EMPTY_ID
    is_enemy: bool = False
    is_boss_or_player: bool = False
    is_combat_participant: bool = True
    is_visible: bool = True
    obj_spawn_timestamp: int = 0

    @classmethod
    def create_environment(cls, obj_id: int) -> 'ObjTargetingData':
        return cls(current_target_id=obj_id)

    @classmethod
    def create_spawned(cls, timestamp: int, parent_id: int, target_id: int, is_enemy: bool, is_boss_or_player: bool) -> 'ObjTargetingData':
        return cls(
            parent_id=parent_id,
            current_target_id=target_id,
            is_enemy=is_enemy,
            is_boss_or_player=is_boss_or_player,
            obj_spawn_timestamp=timestamp,
        )

class TargetingSystem:
    def __init__(self) -> None:
        self.game_obj_data_dct: Dict[int, ObjTargetingData] = {}
        self.default_ids: DefaultIDs = DefaultIDs()

    def create_environment_obj(self, obj_id: int) -> None:
        self.default_ids.environment_id = obj_id
        self.game_obj_data_dct[obj_id] = ObjTargetingData.create_environment(obj_id)

    @property
    def environment_id(self) -> int: return self.default_ids.environment_id
    @property
    def player_id(self) -> int: return self.default_ids.player_id

    def spawn_game_obj(self, timestamp: int, parent_id: int, new_obj_id: int, target_id: int, is_enemy: bool, is_boss_or_player: bool, flag_spawn_boss: bool, flag_spawn_player: bool) -> None:
        # Inherit enemy status if not explicitly overridden by boss/player spawn
        parent_data = self.game_obj_data_dct.get(parent_id)
        final_is_enemy = parent_data.is_enemy if parent_data else is_enemy

        self.game_obj_data_dct[new_obj_id] = ObjTargetingData.create_spawned(timestamp, parent_id, target_id, final_is_enemy, is_boss_or_player)

        if flag_spawn_boss:
            if not self.default_ids.boss1_exists: self.default_ids.boss1_id = new_obj_id
            else: self.default_ids.boss2_id = new_obj_id
        if flag_spawn_player:
            self.default_ids.player_id = new_obj_id

    # ---- State Update Handlers ----

    def update_current_target(self, source_id: int, target_id: int) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.current_target_id = target_id

    def despawn_self(self, source_id: int) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.is_combat_participant = False
            data.is_visible = False

    def teamswap(self, source_id: int) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.is_enemy = not data.is_enemy

    def targetswap_to_parent(self, source_id: int) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.current_target_id = data.parent_id

    def targetswap_to_other_team(self, source_id: int) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.current_target_id = self.default_ids.player_id if data.is_enemy else self.default_ids.boss1_id

    # ---- Lookups ----

    def is_visible(self, obj_id: int) -> bool:
        return self.game_obj_data_dct.get(obj_id, ObjTargetingData()).is_visible

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self.game_obj_data_dct.get(obj_id, ObjTargetingData()).current_target_id

    def is_valid_target(self, obj_id: int) -> bool:
        data = self.game_obj_data_dct.get(obj_id)
        return data is not None and data.is_combat_participant

    def select_targets_for_aoe(self, source_id: int, hits_cross_team: bool, hits_same_team: bool) -> Iterable[int]:
        if not hits_cross_team and not hits_same_team: return
        source_data = self.game_obj_data_dct.get(source_id)
        if not source_data: return

        for obj_id, obj_data in self.game_obj_data_dct.items():
            if not obj_data.is_combat_participant: continue
            is_opposite_team = (obj_data.is_enemy != source_data.is_enemy)
            if (is_opposite_team and hits_cross_team) or (not is_opposite_team and hits_same_team):
                yield obj_id

    def apply_effect(self, effect: Effect, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        t = effect.effect_type
        if t == "update_current_target": self.update_current_target(source_id, target_id)
        elif t == "targetswap_to_other_team": self.targetswap_to_other_team(source_id)
        elif t == "targetswap_to_parent": self.targetswap_to_parent(source_id)
        elif t == "teamswap": self.teamswap(source_id)
        elif t == "despawn_self": self.despawn_self(source_id)