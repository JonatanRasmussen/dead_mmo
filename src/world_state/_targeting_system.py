from dataclasses import dataclass
from typing import Dict, Iterable
from enum import IntFlag, auto

from src.settings import Consts
from ._spell_database import SpellDatabase
from ._spell_system import DefaultIDs
from src.world_state import Behavior, Targeting
from src.world_state._game_obj_system import Status

class TargetingBehavior(IntFlag):
    """Non-combat, non-movement spell flags related to targeting."""
    NONE = 0
    AOE = auto()
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    AURA_APPLY = auto()
    AURA_CANCEL = auto()
    UPDATE_CURRENT_TARGET = auto()

    @classmethod
    def from_behavior(cls, behavior: Behavior) -> "TargetingBehavior":
        """Extract the targeting-related flags from a Behavior."""
        result = cls.NONE

        for flag in cls:
            if (
                flag is not cls.NONE
                and flag.name is not None
                and behavior & getattr(Behavior, flag.name)
            ):
                result |= flag

        return result


@dataclass(slots=True)
class SpellTargetingData:
    """Stores targeting-related data extracted from a Spell."""
    spell_id: int
    spell_sequence: tuple[int, ...]
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


class TargetingSystem:
    """
    Manages spell targeting and object targeting state.
    """

    def __init__(self, spell_database: SpellDatabase) -> None:
        # Maps spell_id -> SpellTargetingData
        self.spell_data_dct: Dict[int, SpellTargetingData] = (
            self._create_initialized_spell_data_dct(spell_database)
        )

        # Maps obj_id -> ObjTargetingData
        self.game_obj_targeting_dct: Dict[int, ObjTargetingData] = {}
        self.default_ids: DefaultIDs = DefaultIDs()

    @staticmethod
    def _create_initialized_spell_data_dct(
        spell_database: SpellDatabase,
    ) -> Dict[int, SpellTargetingData]:
        spell_data_dct: Dict[int, SpellTargetingData] = {}

        for spell in spell_database.get_all_spells():
            flags = TargetingBehavior.from_behavior(spell.flags)

            spell_sequence = (
                tuple(spell.spell_sequence)
                if spell.spell_sequence
                else ()
            )

            is_enemy = bool(flags & TargetingBehavior.SPAWN_BOSS)

            is_boss_or_player = bool(
                flags & TargetingBehavior.SPAWN_BOSS
                or flags & TargetingBehavior.SPAWN_PLAYER
            )

            spell_data_dct[spell.spell_id] = SpellTargetingData(
                spell_id=spell.spell_id,
                spell_sequence=spell_sequence,
                targeting=spell.targeting,
                is_enemy=is_enemy,
                is_boss_or_player=is_boss_or_player,
                flags=flags,
            )

        return spell_data_dct

    def create_environment_obj(self, obj_id: int) -> None:
        """
        Creates the base environment object.
        As the first object created, it bypasses spell templates and parent lookups.
        """
        assert not self.default_ids.environment_exists, f"Environment is already initialized (ID={self.default_ids.environment_id})"
        self.default_ids.environment_id = obj_id
        self.game_obj_targeting_dct[obj_id] = ObjTargetingData(
            parent_id=Consts.EMPTY_ID,
            current_target_id=obj_id, # Mirrors original: env_obj.current_target = obj_id
            is_enemy=False,           # Mirrors original: Faction.NEUTRAL
            is_boss_or_player=False,
            status=Status.ENVIRONMENT,
        )

    def spawn_game_obj(
        self,
        timestamp: int,
        parent_obj_id: int,
        new_obj_id: int,
        spell_id: int,
        target_id: int,
    ) -> None:
        """
        Registers a GameObj into the targeting system.

        Initializes the object's parent and current-target relationships
        and copies its targeting-related properties from the spawning spell
        and parent object.
        """
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        parent_data = self.game_obj_targeting_dct.get(parent_obj_id)

        if parent_data is None:
            return

        # Inherit team/enemy status from parent if applicable.
        if parent_data.status == Status.ENVIRONMENT:
            is_enemy = spell_data.is_enemy
        else:
            is_enemy = parent_data.is_enemy

        self.game_obj_targeting_dct[new_obj_id] = ObjTargetingData(
            parent_id=parent_obj_id,
            current_target_id=target_id,
            is_enemy=is_enemy,
            is_boss_or_player=spell_data.is_boss_or_player,
            status=Status.ALIVE,
        )
        self._update_default_ids(new_obj_id, spell_id)

    def despawn_game_obj(self, obj_id: int) -> None:
        """Removes an object from the combat system (e.g., on despawn)."""
        self.game_obj_targeting_dct.pop(obj_id, None)


    def apply_targeting_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        """
        Applies a spell's combat behavior (damage, healing, GCD, targeting, spawn/despawn) to objects.
        """
        if spell_id not in self.spell_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_targeting_dct.get(source_id)
        if source_data:
            if flags & TargetingBehavior.UPDATE_CURRENT_TARGET:
                source_data.current_target_id = target_id
            if flags & TargetingBehavior.DESPAWN_SELF:
                source_data.status = Status.DESPAWNED

    def get_spell_sequence(self, spell_id: int) -> tuple[int, ...]:
        spell_data = self.spell_data_dct[spell_id]
        return spell_data.spell_sequence

    def is_area_of_effect(self, spell_id: int) -> bool:
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        if flags & TargetingBehavior.AOE:
            return True
        return False

    def has_aura_apply(self, spell_id) -> bool:
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        if flags & TargetingBehavior.AURA_APPLY:
            return True
        return False

    def has_aura_cancel(self, spell_id) -> bool:
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        if flags & TargetingBehavior.AURA_CANCEL:
            return True
        return False

    def is_obj_spawn(self, spell_id) -> bool:
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        if flags & TargetingBehavior.SPAWN_OBJ or flags & TargetingBehavior.SPAWN_BOSS or flags & TargetingBehavior.SPAWN_PLAYER:
            return True
        return False

    def is_visible(self, obj_id: int) -> bool:
        """Checks if an object should be actively rendered on screen."""
        if obj_id not in self.game_obj_targeting_dct:
            return False
        data = self.game_obj_targeting_dct[obj_id]
        return data.status != Status.ENVIRONMENT and data.status != Status.DESPAWNED

    def get_all_active_obj_ids(self) -> Iterable[int]:
        """Returns a collection of all objects currently registered in combat."""
        return self.game_obj_targeting_dct.keys()

    def _is_on_players_team(self, obj_id: int) -> bool:
        data = self.game_obj_targeting_dct.get(obj_id)
        return bool(data is not None and not data.is_enemy)

    def select_aoe_target_ids(self, source_id: int, primary_target_id: int) -> Iterable[int]:
        """ECS replacement of WorldState._select_targets_for_aoe()."""
        source_allied = self._is_on_players_team(source_id)
        target_allied = self._is_on_players_team(primary_target_id)
        for obj_id, data in self.game_obj_targeting_dct.items():
            obj_allied = not data.is_enemy
            team_is_hit = (obj_allied == source_allied) == (source_allied == target_allied)
            if team_is_hit and data.status.is_valid_target and obj_id != primary_target_id:
                yield obj_id

    def decide_targeting(
        self,
        aoe_target_id: int,
        is_aoe_targeting: bool,
        source_id: int,
        spell_id: int,
    ) -> int:
        spell_data = self.spell_data_dct[spell_id]
        targeting = spell_data.targeting

        assert targeting != Targeting.NONE, (
            f"obj {source_id} is casting a spell with targeting=NONE"
        )

        source_data = self.game_obj_targeting_dct[source_id]

        # An enemy is not on the player's team.
        is_on_players_team = not source_data.is_enemy

        if targeting in {Targeting.SELF, Targeting.DEFAULT_FRIENDLY}:
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

        elif targeting == Targeting.DEFAULT_ENEMY:
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
                # Not implemented. For now, assume boss1 always exists.
                target_id = self.default_ids.player_id

        else:
            target_id = self.default_ids.missing_target_id

        # Resolve TARGET_OF_TARGET and TARGET_OF_PARENT.
        if (
            targeting in {Targeting.TARGET_OF_TARGET, Targeting.TARGET_OF_PARENT}
            and Consts.is_valid_id(target_id)
        ):
            target_data = self.game_obj_targeting_dct.get(target_id)

            if (
                target_data is not None
                and Consts.is_valid_id(target_data.current_target_id)
            ):
                target_id = target_data.current_target_id
            else:
                target_id = self.default_ids.missing_target_id

        # A predetermined AoE target overrides all normal targeting logic.
        if is_aoe_targeting:
            target_id = aoe_target_id

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
        """Returns whether an object can currently act as an event source."""
        data = self.game_obj_targeting_dct.get(obj_id)
        return data is not None and data.status.is_valid_source

    def is_valid_target(self, obj_id: int) -> bool:
        """Returns whether an object can currently be targeted by events."""
        data = self.game_obj_targeting_dct.get(obj_id)
        return data is not None and data.status.is_valid_target

    def select_targets_for_aoe(self, source_id: int, target_id: int) -> Iterable[int]:
        """
        Yields all valid target IDs for an AoE spell based on the source and primary target.
        """
        source_data = self.game_obj_targeting_dct.get(source_id)
        target_data = self.game_obj_targeting_dct.get(target_id)
        # Ensure both source and target exist in the targeting dictionary
        if source_data is None or target_data is None:
            return
        source_is_enemy = source_data.is_enemy
        target_is_enemy = target_data.is_enemy
        for obj_id, obj_data in self.game_obj_targeting_dct.items():
            # If source and target are on the same team, it hits that team.
            # If source and target are on opposite teams, it hits the target's team.
            team_is_hit_by_aoe = (
                (obj_data.is_enemy == source_is_enemy) ==
                (source_is_enemy == target_is_enemy)
            )
            if team_is_hit_by_aoe and obj_data.status.is_valid_target and obj_id != target_id:
                yield obj_id