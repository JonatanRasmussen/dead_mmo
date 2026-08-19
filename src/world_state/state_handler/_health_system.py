import math
from dataclasses import dataclass
from typing import Dict
from enum import IntFlag, auto


class HealthBehavior(IntFlag):
    """ Various bitflags that define spell health behavior. """
    NONE = 0
    # HEALTH RELATED STATS
    DAMAGING = auto()
    HEALING = auto()
    IS_CHANNEL = auto()


@dataclass(slots=True)
class SpellHealthData:
    """Stores the health relevant template data extracted from a Spell."""
    power: float = 1.0
    flags: HealthBehavior = HealthBehavior.NONE
    hp: float = 0.0


@dataclass(slots=True)
class ObjHealthData:
    """ECS-style component storing health and resource data for a GameObj."""
    hp: float
    max_hp: float
    spell_modifier: float = 1.0
    is_environment: bool = False

    @classmethod
    def create_environment(cls) -> 'ObjHealthData':
        return cls(
            hp=0.0,
            max_hp=0.0,
            spell_modifier=1.0,
            is_environment=True
        )

    @classmethod
    def create_from_spell(cls, spell_data: SpellHealthData) -> 'ObjHealthData':
        return cls(
            hp=spell_data.hp,
            max_hp=spell_data.hp,
            spell_modifier=1.0,
            is_environment=False
        )


class HealthSystem:
    """
    Manages all health-related logic, resources, and damage/healing.
    """
    def __init__(self, spell_data_dct: Dict[int, SpellHealthData]) -> None:
        self.spell_data_dct: Dict[int, SpellHealthData] = spell_data_dct
        self.game_obj_data_dct: Dict[int, ObjHealthData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjHealthData.create_environment()

    def spawn_game_obj(self, new_obj_id: int, spell_id: int) -> None:
        if spell_id not in self.spell_data_dct or new_obj_id in self.game_obj_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        self.game_obj_data_dct[new_obj_id] = ObjHealthData.create_from_spell(spell_data)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    def apply_health_event(self, source_id: int, spell_id: int, target_id: int) -> None:
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_data_dct.get(source_id)
        target_data = self.game_obj_data_dct.get(target_id)

        # Apply Target Effects
        if source_data and target_data:
            if flags & HealthBehavior.DAMAGING:
                damage_amount = spell_data.power * source_data.spell_modifier
                target_data.hp -= damage_amount
            if flags & HealthBehavior.HEALING:
                healing_amount = spell_data.power * source_data.spell_modifier
                target_data.hp += healing_amount

    # ---- State Lookups ----

    def get_hp(self, obj_id: int) -> float:
        if obj_id in self.game_obj_data_dct:
            return self.game_obj_data_dct[obj_id].hp
        return 0.0

    def get_size(self, obj_id: int) -> float:
        if obj_id not in self.game_obj_data_dct:
            return 0.0
        data = self.game_obj_data_dct[obj_id]
        if data.is_environment:
            return 0.0
        return 0.01 + math.sqrt(0.0001 * abs(data.hp))