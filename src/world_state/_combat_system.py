from dataclasses import dataclass
from typing import Dict, Optional, Iterable
from enum import IntFlag, auto
import math

from src.settings import Consts
from ._spell_database import SpellDatabase
from src.world_state import Behavior
from src.world_state._game_obj_system import Status

class CombatBehavior(IntFlag):
    """ Various bitflags that define spell combat behavior. """
    NONE = 0
    # COMBATSTATS
    DAMAGING = auto()
    HEALING = auto()
    # STATE UPDATE
    IS_CHANNEL = auto()
    # TARGETING
    AOE = auto()
    UPDATE_CURRENT_TARGET = auto()
    # VALIDATION
    TRIGGER_GCD = auto()
    DENY_IF_CASTING = auto()
    @classmethod
    def from_behavior(cls, behavior: Behavior) -> "CombatBehavior":
        """Extract the combat-related flags from a Behavior."""
        result = cls.NONE
        for flag in cls:
            if flag is not cls.NONE and flag.name is not None and behavior & getattr(Behavior, flag.name):
                result |= flag
        return result
@dataclass(slots=True)
class SpellCombatTemplate:
    """Stores the extracted combat stats from a Spell's spawned_obj template."""
    hp: float
    gcd_mod: float
    is_enemy: bool
    is_boss_or_player: bool
@dataclass(slots=True)
class SpellCombatData:
    """Stores only the combat-relevant data extracted from a Spell."""
    power: float
    flags: CombatBehavior
    spawn_template: Optional[SpellCombatTemplate] = None
@dataclass(slots=True)
class ObjCombatData:
    """ECS-style component storing combat and resource data for a GameObj."""
    hp: float
    max_hp: float
    gcd_mod: float = 1.0
    spell_modifier: float = 1.0
    gcd_start: int = -10000
    parent_id: int = Consts.EMPTY_ID
    current_target_id: int = Consts.EMPTY_ID
    is_enemy: bool = False
    is_boss_or_player: bool = False
    is_environment: bool = False
    status: Status = Status.EMPTY
class CombatSystem:
    """
    Manages all combat-related logic, resources, damage/healing, and GCDs.
    """
    def __init__(self, spell_database: SpellDatabase) -> None:
        # Maps spell_id -> SpellCombatData
        self.spell_data_dct: Dict[int, SpellCombatData] = self._create_initialized_spell_data_dct(spell_database)
        # Maps obj_id -> ObjCombatData
        self.game_obj_combat_dct: Dict[int, ObjCombatData] = {}
    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> Dict[int, SpellCombatData]:
        """
        Loads combat-relevant data from a SpellDatabase into memory.
        Extracts spawn templates so the CombatSystem can handle spawning internally.
        """
        spell_data_dct = {}
        for spell in spell_database.get_all_spells():
            spawn_template = None
            # Extract template data if the spell spawns an object
            if spell.spawned_obj is not None and spell.spawned_obj.game_obj is not None:
                spawned_obj = spell.spawned_obj.game_obj
                # Determine if it's a boss or player based on spell flags
                is_boss_or_player = bool(spell.flags & (Behavior.SPAWN_BOSS | Behavior.SPAWN_PLAYER))
                spawn_template = SpellCombatTemplate(
                    hp=spawned_obj._res.hp,
                    gcd_mod=spawned_obj.gcd_mod,
                    is_enemy=not spawned_obj.is_on_players_team,
                    is_boss_or_player=is_boss_or_player,
                )
            spell_data_dct[spell.spell_id] = SpellCombatData(
                power=spell.power,
                flags=CombatBehavior.from_behavior(spell.flags),
                spawn_template=spawn_template
            )
        return spell_data_dct
    def create_environment_obj(self, obj_id: int) -> None:
        """
        Creates the base environment object.
        As the first object created, it bypasses spell templates and parent lookups.
        """
        self.game_obj_combat_dct[obj_id] = ObjCombatData(
            hp=0.0,                 # Environment typically doesn't need HP (or use float('inf'))
            max_hp=0.0,
            gcd_mod=1.0,
            spell_modifier=1.0,
            gcd_start=-10000,
            parent_id=Consts.EMPTY_ID,
            current_target_id=obj_id, # Mirrors original: env_obj.current_target = obj_id
            is_enemy=False,           # Mirrors original: Faction.NEUTRAL
            is_boss_or_player=False,
            is_environment=True,
            status=Status.ENVIRONMENT,
        )
    def spawn_game_obj(self, timestamp: int, parent_obj_id: int, new_obj_id: int, spell_id: int, target_id: int) -> None:
        """
        Registers a GameObj into the combat system.
        Fully handles the spawn logic by looking up the spell's spawn template.
        """
        if spell_id not in self.spell_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        if spell_data.spawn_template is None:
            return
        template = spell_data.spawn_template
        # Inherit team/enemy status from parent if applicable
        parent_data = self.game_obj_combat_dct[parent_obj_id]
        if parent_data.is_environment:
            is_enemy = template.is_enemy
        else:
            is_enemy = parent_data.is_enemy
        self.game_obj_combat_dct[new_obj_id] = ObjCombatData(
            hp=template.hp,
            max_hp=template.hp,
            gcd_mod=template.gcd_mod,
            spell_modifier=1.0,
            gcd_start=timestamp,
            parent_id=parent_obj_id,
            current_target_id=target_id,
            is_enemy=is_enemy,
            is_boss_or_player=template.is_boss_or_player,
            is_environment=False,
            status=Status.ALIVE,
        )
    def despawn_game_obj(self, obj_id: int) -> None:
        """Removes an object from the combat system (e.g., on despawn)."""
        self.game_obj_combat_dct.pop(obj_id, None)
    def apply_combat_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        """
        Applies a spell's combat behavior (damage, healing, GCD, targeting) to objects.
        """
        if spell_id not in self.spell_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_combat_dct.get(source_id)
        target_data = self.game_obj_combat_dct.get(target_id)
        # Apply Source Effects
        if source_data:
            if flags & CombatBehavior.UPDATE_CURRENT_TARGET:
                source_data.current_target_id = target_id
            if flags & CombatBehavior.TRIGGER_GCD:
                source_data.gcd_start = timestamp
        # Apply Target Effects (Requires both source and target to calculate modifiers)
        if source_data and target_data:
            if flags & CombatBehavior.DAMAGING:
                damage_amount = spell_data.power * source_data.spell_modifier
                target_data.hp -= damage_amount
            if flags & CombatBehavior.HEALING:
                healing_amount = spell_data.power * source_data.spell_modifier
                target_data.hp += healing_amount
                # Optional: Clamp HP to max_hp
                #if target_data.hp > target_data.max_hp:
                #    target_data.hp = target_data.max_hp
    def get_gcd_progress(self, obj_id: int, current_time: int) -> float:
        """Returns the GCD progress of an object as a float between 0.0 and 1.0."""
        if obj_id not in self.game_obj_combat_dct:
            return 1.0
        data = self.game_obj_combat_dct[obj_id]
        gcd_duration = Consts.BASE_GCD * data.gcd_mod
        if gcd_duration <= 0:
            return 1.0
        progress = (current_time - data.gcd_start) / gcd_duration
        return min(1.0, max(0.0, progress))
    def is_gcd_ready(self, obj_id: int, current_time: int) -> bool:
        """Checks if an object's Global Cooldown is finished."""
        return self.get_gcd_progress(obj_id, current_time) >= 1.0
    def get_hp(self, obj_id: int) -> float:
        """Helper to get current HP."""
        if obj_id in self.game_obj_combat_dct:
            return self.game_obj_combat_dct[obj_id].hp
        return 0.0
    def get_status(self, obj_id: int) -> Status:
        """Helper to get current status."""
        if obj_id in self.game_obj_combat_dct:
            return self.game_obj_combat_dct[obj_id].status
        return Status.EMPTY

    def get_size(self, obj_id: int) -> float:
        """Returns the rendering scale/hitbox size based on current HP."""
        if obj_id not in self.game_obj_combat_dct:
            return 0.0
        data = self.game_obj_combat_dct[obj_id]
        if data.is_environment:
            return 0.0
        return 0.01 + math.sqrt(0.0001 * abs(data.hp))

    def is_visible(self, obj_id: int) -> bool:
        """Checks if an object should be actively rendered on screen."""
        if obj_id not in self.game_obj_combat_dct:
            return False
        data = self.game_obj_combat_dct[obj_id]
        return not data.is_environment and data.status != Status.DESPAWNED

    def get_all_active_obj_ids(self) -> Iterable[int]:
        """Returns a collection of all objects currently registered in combat."""
        return self.game_obj_combat_dct.keys()