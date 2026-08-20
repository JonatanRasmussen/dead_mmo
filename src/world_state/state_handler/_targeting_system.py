from dataclasses import dataclass
from typing import Dict, Iterable
from enum import IntFlag, auto, Enum

from src.settings import Consts


class Targeting(Enum):
    """ Defines targeting behavior for spell """
    NONE = 0
    SELF = auto()
    USE_EVENT_TARGET = auto()
    TARGET = auto()
    TARGET_OF_TARGET = auto()
    PARENT = auto()
    TARGET_OF_PARENT = auto()
    DEFAULT_SAME_TEAM = auto()
    DEFAULT_CROSS_TEAM = auto()
    TAB_TO_NEXT = auto()

class Status(Enum):
    """ Various status effects that game objects can have. """
    EMPTY = 0  # Should never be used outside initialization
    ENVIRONMENT = auto()  # Special case used only by ENVIRONMENT objs
    NEW_PLAYER_OBJ = auto()  # Special case used temporarily by newly spawned players
    NEW_BOSS_OBJ = auto()  # Special case used temporarily by newly spawned bosses
    ALIVE = auto()  # Default status used to indicate the absence of other status effects
    INACTIVE = auto()  # Not yet engaged in combat, cannot be source or target of events
    DESPAWNED = auto()  # Permamently removed from combat, cannot be source or target of events
    BANISHED = auto()  # Temporarily removed from combat, cannot be source or target of events
    CASTING = auto()  # to-do: document this
    CHANNELING = auto()  # to-do: document this
    ROOTED = auto()  # to-do: document this
    STUNNED = auto()  # to-do: document this

    @property
    def is_valid_source(self) -> bool:
        return not self in {
            Status.DESPAWNED,
            Status.BANISHED,
        }

    @property
    def is_valid_target(self) -> bool:
        return not self in {
            Status.ENVIRONMENT,
            Status.DESPAWNED,
            Status.BANISHED,
        }

@dataclass(slots=True)
class DefaultIDs:
    environment_id: int = Consts.EMPTY_ID
    player_id: int = Consts.EMPTY_ID
    boss1_id: int = Consts.EMPTY_ID
    boss2_id: int = Consts.EMPTY_ID

    @property
    def missing_target_id(self) -> int:
        return self.environment_id
    @property
    def default_allied_id(self) -> int:
        if self.player_exists:
            return self.player_id
        return self.missing_target_id
    @property
    def default_hostile_id(self) -> int:
        if self.boss1_exists:
            return self.boss1_id
        return self.missing_target_id

    @property
    def environment_exists(self) -> bool:
        return Consts.is_valid_id(self.environment_id)
    @property
    def player_exists(self) -> bool:
        return Consts.is_valid_id(self.player_id)
    @property
    def boss1_exists(self) -> bool:
        return Consts.is_valid_id(self.boss1_id)
    @property
    def boss2_exists(self) -> bool:
        return Consts.is_valid_id(self.boss2_id)


class TargetingBehavior(IntFlag):
    """Non-combat, non-movement spell flags related to targeting."""
    NONE = 0
    AOE = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    UPDATE_CURRENT_TARGET = auto()


@dataclass(slots=True)
class SpellTargetingData:
    """Stores targeting-related data extracted from a Spell."""
    spell_id: int
    targeting: Targeting
    is_enemy: bool = False
    is_boss_or_player: bool = False
    flags: TargetingBehavior = TargetingBehavior.NONE


@dataclass(slots=True)
class ObjTargetingData:
    """Stores targeting and state data for a GameObj."""
    parent_id: int = Consts.EMPTY_ID
    current_target_id: int = Consts.EMPTY_ID
    is_enemy: bool = False
    is_boss_or_player: bool = False
    status: Status = Status.EMPTY
    obj_spawn_timestamp: int = 0

    @classmethod
    def create_environment(cls, obj_id: int) -> 'ObjTargetingData':
        return cls(
            parent_id=Consts.EMPTY_ID,
            current_target_id=obj_id,
            is_enemy=False,
            is_boss_or_player=False,
            status=Status.ENVIRONMENT,
            obj_spawn_timestamp=0,
        )

    @classmethod
    def create_from_spell(
        cls, timestamp: int, parent_obj_id: int, target_id: int,
        parent_data: 'ObjTargetingData', spell_data: SpellTargetingData
    ) -> 'ObjTargetingData':
        is_enemy = spell_data.is_enemy if parent_data.status == Status.ENVIRONMENT else parent_data.is_enemy
        return cls(
            parent_id=parent_obj_id,
            current_target_id=target_id,
            is_enemy=is_enemy,
            is_boss_or_player=spell_data.is_boss_or_player,
            status=Status.ALIVE,
            obj_spawn_timestamp=timestamp,
        )


class TargetingSystem:
    """
    Manages spell targeting and object targeting state.
    """
    def __init__(self, spell_data_dct: Dict[int, SpellTargetingData]) -> None:
        self.spell_data_dct: Dict[int, SpellTargetingData] = spell_data_dct
        self.game_obj_data_dct: Dict[int, ObjTargetingData] = {}
        self.default_ids: DefaultIDs = DefaultIDs()

    def create_environment_obj(self, obj_id: int) -> None:
        assert not self.default_ids.environment_exists, f"Environment is already initialized (ID={self.default_ids.environment_id})"
        self.default_ids.environment_id = obj_id
        self.game_obj_data_dct[obj_id] = ObjTargetingData.create_environment(obj_id)

    @property
    def environment_id(self) -> int:
        return self.default_ids.environment_id

    @property
    def player_id(self) -> int:
        return self.default_ids.player_id

    def spawn_game_obj(
        self,
        timestamp: int,
        parent_obj_id: int,
        new_obj_id: int,
        spell_id: int,
        target_id: int,
    ) -> None:
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        parent_data = self.game_obj_data_dct.get(parent_obj_id)

        if parent_data is None:
            return

        self.game_obj_data_dct[new_obj_id] = ObjTargetingData.create_from_spell(
            timestamp, parent_obj_id, target_id, parent_data, spell_data
        )
        self._update_default_ids(new_obj_id, spell_id)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)


    def apply_targeting_event(self, source_id: int, spell_id: int, target_id: int) -> None:
        if spell_id not in self.spell_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_data_dct.get(source_id)
        if source_data:
            if flags & TargetingBehavior.UPDATE_CURRENT_TARGET:
                source_data.current_target_id = target_id
            if flags & TargetingBehavior.DESPAWN_SELF:
                source_data.status = Status.DESPAWNED

    def is_area_of_effect(self, spell_id: int) -> bool:
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        if flags & TargetingBehavior.AOE:
            return True
        return False

    def is_obj_spawn(self, spell_id) -> bool:
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        if flags & TargetingBehavior.SPAWN_OBJ or flags & TargetingBehavior.SPAWN_BOSS or flags & TargetingBehavior.SPAWN_PLAYER:
            return True
        return False

    def is_visible(self, obj_id: int) -> bool:
        if obj_id not in self.game_obj_data_dct:
            return False
        data = self.game_obj_data_dct[obj_id]
        return data.status != Status.ENVIRONMENT and data.status != Status.DESPAWNED

    def get_all_active_obj_ids(self) -> Iterable[int]:
        return self.game_obj_data_dct.keys()

    def _is_on_players_team(self, obj_id: int) -> bool:
        data = self.game_obj_data_dct.get(obj_id)
        return bool(data is not None and not data.is_enemy)

    def get_current_target_for_obj(self, obj_id) -> int:
        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return Consts.EMPTY_ID
        return obj_data.current_target_id

    def select_aoe_target_ids(self, source_id: int, primary_target_id: int) -> Iterable[int]:
        source_allied = self._is_on_players_team(source_id)
        target_allied = self._is_on_players_team(primary_target_id)
        for obj_id, data in self.game_obj_data_dct.items():
            obj_allied = not data.is_enemy
            team_is_hit = (obj_allied == source_allied) == (source_allied == target_allied)
            if team_is_hit and data.status.is_valid_target and obj_id != primary_target_id:
                yield obj_id

    def decide_event_targeting(self, source_id: int, spell_id: int, undecided_target_id: int) -> int:
        spell_data = self.spell_data_dct[spell_id]
        targeting = spell_data.targeting

        assert targeting != Targeting.NONE or (spell_data.flags & TargetingBehavior.AOE), (
            f"obj {source_id} is casting a spell with neither targeting=NONE or AOE-behavior"
        )

        source_data = self.game_obj_data_dct[source_id]
        is_on_players_team = not source_data.is_enemy

        if targeting in {Targeting.SELF, Targeting.DEFAULT_SAME_TEAM}:
            target_id = source_id
        elif (
            targeting in {Targeting.TARGET, Targeting.TARGET_OF_TARGET}
            and Consts.is_valid_id(source_data.current_target_id)
        ):
            target_id = source_data.current_target_id
        elif (
            targeting in {Targeting.PARENT, Targeting.TARGET_OF_PARENT}
            and Consts.is_valid_id(source_data.parent_id)
        ):
            target_id = source_data.parent_id
        elif targeting == Targeting.DEFAULT_CROSS_TEAM:
            if is_on_players_team:
                target_id = self.default_ids.boss1_id
            else:
                target_id = self.default_ids.player_id
        elif targeting == Targeting.TAB_TO_NEXT:
            if not is_on_players_team:
                target_id = self.default_ids.player_id
            elif (
                source_data.current_target_id == self.default_ids.boss1_id
                and self.default_ids.boss2_exists
            ):
                target_id = self.default_ids.boss2_id
            elif Consts.is_valid_id(self.default_ids.boss1_id):
                target_id = self.default_ids.boss1_id
            else:
                target_id = self.default_ids.player_id
        else:
            target_id = self.default_ids.missing_target_id

        if (
            targeting in {Targeting.TARGET_OF_TARGET, Targeting.TARGET_OF_PARENT}
            and Consts.is_valid_id(target_id)
        ):
            target_data = self.game_obj_data_dct.get(target_id)
            if (
                target_data is not None
                and Consts.is_valid_id(target_data.current_target_id)
            ):
                target_id = target_data.current_target_id
            else:
                target_id = self.default_ids.missing_target_id

        if targeting == Targeting.USE_EVENT_TARGET:
            target_id = undecided_target_id

        return target_id

    def _update_default_ids(self, obj_id: int, spell_id: int) -> None:
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        if flags & TargetingBehavior.SPAWN_BOSS:
            if not self.default_ids.boss1_exists:
                self.default_ids.boss1_id = obj_id
            else:
                assert not self.default_ids.boss2_exists, "Second boss already exists."
                self.default_ids.boss2_id = obj_id
        if flags & TargetingBehavior.SPAWN_PLAYER:
            assert not self.default_ids.player_exists, "Player already exists."
            self.default_ids.player_id = obj_id

    def is_valid_source(self, obj_id: int) -> bool:
        data = self.game_obj_data_dct.get(obj_id)
        return data is not None and data.status.is_valid_source

    def is_valid_target(self, obj_id: int) -> bool:
        data = self.game_obj_data_dct.get(obj_id)
        return data is not None and data.status.is_valid_target

    def select_targets_for_aoe(self, source_id: int, target_id: int) -> Iterable[int]:
        source_data = self.game_obj_data_dct.get(source_id)
        target_data = self.game_obj_data_dct.get(target_id)
        if source_data is None or target_data is None:
            return
        source_is_enemy = source_data.is_enemy
        target_is_enemy = target_data.is_enemy
        for obj_id, obj_data in self.game_obj_data_dct.items():
            team_is_hit_by_aoe = (
                (obj_data.is_enemy == source_is_enemy) ==
                (source_is_enemy == target_is_enemy)
            )
            if team_is_hit_by_aoe and obj_data.status.is_valid_target:
                yield obj_id