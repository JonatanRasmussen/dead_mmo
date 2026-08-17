import copy
import json
from typing import Iterable, Optional
from dataclasses import dataclass, field
from enum import IntFlag, Enum, auto

from src.settings import Consts
from src.utils.copy_utils import CopyTools
from src.world_state._spell_system import Behavior
from src.world_state._spell_database import SpellDatabase
from ._controls_data import Controls, InputTranslator, KeyPresses, LOADOUT_KEY_TO_INDEX_MAP


class Outcome(Enum):
    EMPTY = 0
    SUCCESS = auto()
    OUT_OF_RANGE = auto()
    GCD_NOT_READY = auto()
    NO_TARGET_WAS_SELECTED = auto()
    SOURCE_IS_DISABLED = auto()
    TARGET_IS_INVALID = auto()
    AURA_NO_LONGER_EXISTS = auto()

    @property
    def is_success(self) -> bool:
        return self in {Outcome.SUCCESS}


@dataclass(slots=True)
class UpcomingEvent:
    event_id: int = Consts.EMPTY_ID
    timestamp: int = Consts.EMPTY_TIMESTAMP
    priority: int = 0

    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    outcome: Outcome = Outcome.EMPTY

    spell_modifier: float = 1.0

    aura_id: int = Consts.EMPTY_ID
    aura_origin_spell_id: int = Consts.EMPTY_ID
    is_spell_sequence: bool = False
    is_aoe_targeting: bool = False

    @classmethod
    def deserialize(cls, data: str) -> 'UpcomingEvent':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            event_id=d["eid"],
            timestamp=d["ts"],
            priority=d["pr"],
            source_id=d["sid"],
            spell_id=d["sp"],
            target_id=d["tid"],
            spell_modifier=d["sm"],
            aura_id=d["aid"],
            aura_origin_spell_id=d["aos"],
            is_spell_sequence=d["seq"],
            is_aoe_targeting=d["aoe"]
        )

    def serialize(self) -> str:
        return json.dumps({
            "eid": self.event_id,
            "ts": self.timestamp,
            "pr": self.priority,
            "sid": self.source_id,
            "sp": self.spell_id,
            "tid": self.target_id,
            "sm": self.spell_modifier,
            "aid": self.aura_id,
            "aos": self.aura_origin_spell_id,
            "seq": self.is_spell_sequence,
            "aoe": self.is_aoe_targeting
        })

    @property
    def outcome_is_valid(self) -> bool:
        return self.outcome.is_success

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] {self.outcome} (obj_{self.source_id:04d} uses spell_{self.spell_id:04d} on obj_{self.target_id:04d}.)"

    @property
    def key(self) -> tuple[int, int, int, int, int]:
        return (self.timestamp, self.priority, self.source_id, self.target_id, self.spell_id)

    @property
    def has_target(self) -> bool:
        return Consts.is_valid_id(self.target_id)

    @property
    def is_aura_tick(self) -> bool:
        return Consts.is_valid_id(self.aura_origin_spell_id)

    def finalize_event(self, source_id: int, target_id: int, outcome: Outcome) -> 'UpcomingEvent':
        f_event = self.create_copy()
        f_event.source_id = source_id
        f_event.target_id = target_id
        f_event.outcome = outcome
        return f_event

    def create_copy(self) -> 'UpcomingEvent':
        return CopyTools.full_copy(self)


class EventBehavior(IntFlag):
    """ Various bitflags that define spell combat and spawn behavior. """
    NONE = 0
    # OBJ SPAWN
    SPAWN_BOSS = auto()
    SPAWN_PLAYER = auto()
    SPAWN_OBJ = auto()
    DESPAWN_SELF = auto()
    # AURA FLAGS
    AURA_APPLY = auto()
    AURA_CANCEL = auto()
    # AoE
    AOE = auto()

    @classmethod
    def from_behavior(cls, behavior: Behavior) -> "EventBehavior":
        """Extract the combat/spawn-related flags from a Behavior."""
        result = cls.NONE
        for flag in cls:
            if flag is cls.NONE or flag.name is None:
                continue
            source_flag = getattr(Behavior, flag.name, None)
            if source_flag is not None and behavior & source_flag:
                result |= flag
        return result


@dataclass(slots=True)
class SpellEventData:
    spell_id: int = Consts.EMPTY_ID
    aura_effect_id: int = Consts.EMPTY_ID

    spell_sequence: tuple[int, ...] = ()
    flags: EventBehavior = EventBehavior.NONE

    # Input/Script Controls Mapping
    spell_bindings: list[int] = field(default_factory=list)
    controls: tuple[Controls, ...] = ()


@dataclass(slots=True)
class ObjEventData:
    """ECS-style component storing per-obj input-to-spell mappings and scripted controls."""
    spell_bindings: list[int]
    controls: tuple[Controls, ...] = ()


class EventSystem:
    def __init__(self, spell_database: SpellDatabase) -> None:
        self._spell_data_dct: dict[int, SpellEventData] = self._create_initialized_spell_data_dct(spell_database)
        self.game_obj_data_dct: dict[int, ObjEventData] = {}

    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> dict[int, SpellEventData]:
        spell_data_dct = {}
        for spell in spell_database.get_all_spells():
            spell_sequence = (
                tuple(spell.spell_sequence)
                if spell.spell_sequence
                else ()
            )

            spell_bindings: list[int] = []
            controls_tuple: tuple[Controls, ...] = ()

            # Extract configuration from the game_obj loadout, strictly for initial setup.
            if spell.spawned_obj is not None:
                game_obj = spell.spawned_obj.game_obj
                if getattr(game_obj, "_loadout", None) is not None:
                    spell_bindings = list(game_obj._loadout.spell_ids)
                controls_tuple = spell.spawned_obj.obj_controls or ()

            spell_data_dct[spell.spell_id] = SpellEventData(
                spell_id=spell.spell_id,
                aura_effect_id=spell.effect_id,
                spell_sequence=spell_sequence,
                flags=EventBehavior.from_behavior(spell.flags),
                spell_bindings=spell_bindings,
                controls=controls_tuple,
            )
        return spell_data_dct

    def spawn_game_obj(self, new_obj_id: int, spell_id: int) -> None:
        template = self._spell_data_dct.get(spell_id)
        if template is None or not template.spell_bindings:
            return
        if new_obj_id in self.game_obj_data_dct:   # idempotent: never double-register
            return

        self.game_obj_data_dct[new_obj_id] = ObjEventData(
            spell_bindings=list(template.spell_bindings),
            controls=template.controls,
        )

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjEventData(
            spell_bindings=[Consts.EMPTY_ID] * len(LOADOUT_KEY_TO_INDEX_MAP),
            controls=()
        )

    def get_spell_ids_for_inputs(self, obj_id: int, hardware_inputs: list[str], timestamp: int) -> Iterable[int]:
        if not hardware_inputs:
            return

        key_presses = InputTranslator.translate_to_keypresses(hardware_inputs)
        if key_presses == KeyPresses.NONE:
            return

        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.spell_bindings:
            return

        # Direct translation without relying on Loadout objects
        for key_flag, index in LOADOUT_KEY_TO_INDEX_MAP.items():
            if key_flag & key_presses:
                spell_id = obj_data.spell_bindings[index]
                if Consts.is_valid_id(spell_id):
                    yield spell_id

    def get_scripted_spells(self, obj_id: int, spawn_timestamp: int) -> Iterable[tuple[int, int, int]]:
        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.controls or not obj_data.spell_bindings:
            return

        for original_controls in obj_data.controls:
            # Create a copy and apply the offset
            controls = original_controls.create_copy()
            controls.increase_offset(spawn_timestamp)

            priority = 0
            for key_flag, index in LOADOUT_KEY_TO_INDEX_MAP.items():
                if key_flag in controls.key_presses:
                    spell_id = obj_data.spell_bindings[index]
                    if Consts.is_valid_id(spell_id):
                        priority += 1
                        yield spell_id, controls.ingame_time, priority

    def is_obj_spawn(self, spell_id: int) -> bool:
        return bool(
            bool(self._spell_data_dct[spell_id].flags & EventBehavior.SPAWN_OBJ) or
            bool(self._spell_data_dct[spell_id].flags & EventBehavior.SPAWN_PLAYER) or
            bool(self._spell_data_dct[spell_id].flags & EventBehavior.SPAWN_BOSS)
        )

    def is_despawn_self(self, spell_id: int) -> bool:
        return bool(self._spell_data_dct[spell_id].flags & EventBehavior.DESPAWN_SELF)

    def has_aura_apply(self, spell_id: int) -> bool:
        return bool(self._spell_data_dct[spell_id].flags & EventBehavior.AURA_APPLY)

    def has_aura_cancel(self, spell_id: int) -> bool:
        return bool(self._spell_data_dct[spell_id].flags & EventBehavior.AURA_CANCEL)

    def is_aoe(self, spell_id: int) -> bool:
        return bool(self._spell_data_dct[spell_id].flags & EventBehavior.AOE)

    def get_spell_sequence(self, spell_id: int) -> tuple[int, ...]:
        spell_data = self._spell_data_dct[spell_id]
        return spell_data.spell_sequence