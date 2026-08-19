import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Union
from enum import IntFlag, auto
import json

from src.utils import CopyTools
from src.settings import Consts, HardwareInputConsts


class KeyPresses(IntFlag):
    """ Various bitflags representing a set of keypress game inputs. """
    NONE = 0

    ABILITY_1 = auto()
    ABILITY_2 = auto()
    ABILITY_3 = auto()
    ABILITY_4 = auto()

    SWAP_TARGET = auto()

    START_MOVE_UP = auto()
    STOP_MOVE_UP = auto()
    START_MOVE_LEFT = auto()
    STOP_MOVE_LEFT = auto()
    START_MOVE_DOWN = auto()
    STOP_MOVE_DOWN = auto()
    START_MOVE_RIGHT = auto()
    STOP_MOVE_RIGHT = auto()


class InputTranslator:

    _HARDWARE_TO_KEYPRESSES: dict[str, KeyPresses] = {
        HardwareInputConsts.KEYBOARD_KEYDOWN_1: KeyPresses.ABILITY_1,
        HardwareInputConsts.KEYBOARD_KEYDOWN_2: KeyPresses.ABILITY_2,
        HardwareInputConsts.KEYBOARD_KEYDOWN_3: KeyPresses.ABILITY_3,
        HardwareInputConsts.KEYBOARD_KEYDOWN_4: KeyPresses.ABILITY_4,

        HardwareInputConsts.KEYBOARD_KEYDOWN_TAB: KeyPresses.SWAP_TARGET,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_UP: KeyPresses.START_MOVE_UP,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_UP: KeyPresses.STOP_MOVE_UP,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_LEFT: KeyPresses.START_MOVE_LEFT,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_LEFT: KeyPresses.STOP_MOVE_LEFT,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_DOWN: KeyPresses.START_MOVE_DOWN,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_DOWN: KeyPresses.STOP_MOVE_DOWN,

        HardwareInputConsts.KEYBOARD_KEYDOWN_ARROW_RIGHT: KeyPresses.START_MOVE_RIGHT,
        HardwareInputConsts.KEYBOARD_KEYUP_ARROW_RIGHT: KeyPresses.STOP_MOVE_RIGHT,
    }
    @staticmethod
    def translate_to_keypresses(inputs: Iterable[str]) -> KeyPresses:
        result = KeyPresses.NONE

        for input_const in inputs:
            try:
                result |= InputTranslator._HARDWARE_TO_KEYPRESSES[input_const]
            except KeyError as exc:
                raise ValueError(f"Unknown input const: {input_const}") from exc

        return result


@dataclass(slots=True)
class Controls:
    """ Keypresses for a given timestamp. Used to make game objects initiate a spellcast. """
    obj_id: int = Consts.EMPTY_ID
    timeline_timestamp: int = Consts.EMPTY_TIMESTAMP
    _offset: int = 0

    key_presses: KeyPresses = KeyPresses.NONE

    @classmethod
    def deserialize(cls, data: str) -> 'Controls':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            obj_id=d["obj_id"],
            timeline_timestamp=d["timestamp"],
            _offset=d["offset"],
            key_presses=KeyPresses(d["keypress"])  # Cast the integer back to the KeyPresses Enum type
        )
    def serialize(self) -> str:
        kp_value = self.key_presses.value if hasattr(self.key_presses, "value") else self.key_presses  # We extract the value from KeyPresses if it is an Enum, otherwise use it directly
        data = {
            "obj_id": self.obj_id,
            "timestamp": self.timeline_timestamp,
            "offset": self._offset,
            "keypress": kp_value
        }
        return json.dumps(data)

    def debug_print(self) -> None:
        """Displays the value of a Controls object for terminal debugging purposes."""
        kp_value = self.key_presses.value if hasattr(self.key_presses, "value") else self.key_presses
        kp_readable = self.key_presses.name if self.key_presses.name else str(self.key_presses)
        print(f"Controls(obj_id={self.obj_id}, timestamp={self.timeline_timestamp}, time_offset={self._offset}, keypress={kp_readable}[{kp_value}])")

    @property
    def get_key_for_controls(self) -> tuple[int, int]:
        return (self.ingame_time, self.obj_id)

    @property
    def is_empty(self) -> bool:
        return self.key_presses == KeyPresses.NONE

    @property
    def ingame_time(self) -> int:
        return self.timeline_timestamp + self._offset

    @property
    def has_valid_timestamp(self) -> bool:
        return self.ingame_time != Consts.EMPTY_TIMESTAMP

    def increase_offset(self, additional_offset: int) -> None:
        assert self._offset == 0, "Controls has been offset more than once, is this intentional?"
        self._offset += additional_offset

    def create_copy(self) -> 'Controls':
        return CopyTools.full_copy(self)

# Calculate once when the module is imported as a performance optimization.
LOADOUT_KEY_TO_INDEX_MAP: dict[KeyPresses, int] = {
    key: key.value.bit_length() - 1 for key in KeyPresses if key != KeyPresses.NONE
}

@dataclass(slots=True)
class Loadout:
    """Used by GameObjs to map controls inputs to spell events"""

    spawn_timestamp: int = Consts.EMPTY_TIMESTAMP
    spell_ids: list[int] = field(default_factory=lambda: [Consts.EMPTY_ID] * len(LOADOUT_KEY_TO_INDEX_MAP))
    ability_cd_start: list[int] = field(default_factory=lambda: [Consts.EMPTY_TIMESTAMP] * len(LOADOUT_KEY_TO_INDEX_MAP))
    gcd_start: int = -1_000

    @classmethod
    def deserialize(cls, data: str) -> 'Loadout':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            spawn_timestamp=d["ts"],
            spell_ids=d["ids"],
            ability_cd_start=d["cds"],
            gcd_start=d["gcd"]
        )
    def serialize(self) -> str:
        return json.dumps({
            "ts": self.spawn_timestamp,
            "ids": self.spell_ids,
            "cds": self.ability_cd_start,
            "gcd": self.gcd_start
        })

    @classmethod
    def create_from_bindings(cls, bindings: dict[KeyPresses, int]) -> 'Loadout':
        """Creates and configures a Loadout from a dictionary of bindings."""
        loadout = cls()
        for key, spell_id in bindings.items():
            loadout.bind_spell(key, spell_id)
        return loadout

    def bind_spell(self, key_presses: KeyPresses, spell_id: int) -> 'Loadout':
        """Binds each keypress in key_presses to spell_id"""
        for flag in LOADOUT_KEY_TO_INDEX_MAP:
            if flag in key_presses:
                index = LOADOUT_KEY_TO_INDEX_MAP[flag]
                self.spell_ids[index] = spell_id
        return self  # Returns self to allow chaining

    def convert_controls_to_spell_ids(self, controls: Controls, obj_id: int) -> Iterable[int]:
        """Fast conversion using direct list indexing."""
        assert not controls.is_empty, f"Controls for {obj_id} is empty."
        for key_flag in LOADOUT_KEY_TO_INDEX_MAP:
            if key_flag in controls.key_presses:
                spell_id = self.spell_ids[LOADOUT_KEY_TO_INDEX_MAP[key_flag]]
                assert Consts.is_valid_id(spell_id), f"Invalid spell ID for {obj_id}: {key_flag.name}_id"
                yield spell_id

    def copy(self) -> "Loadout":
        """Returns a fully independent copy of this Loadout."""
        return CopyTools.full_copy(self)


class CastingBehavior(IntFlag):
    """ Various bitflags that define spell casting and cooldown behavior. """
    NONE = 0
    # VALIDATION & COOLDOWNS
    TRIGGER_GCD = auto()
    TRIGGER_COOLDOWN = auto()
    DENY_IF_CASTING = auto()
    # STATE UPDATE
    START_CHANNEL = auto()
    STOP_CHANNEL = auto()


@dataclass(slots=True)
class SpellCastingData:
    """Stores the casting and cooldown-relevant template data extracted from a Spell."""
    flags: CastingBehavior = CastingBehavior.NONE
    spell_sequence: tuple[int, ...] = ()
    timeline: Mapping[int, Union[int, tuple[int, ...]]] = field(default_factory=dict)
    effect_id: int = 0
    duration: int = 0
    ticks: int = 1
    base_cooldown: float = 0.0
    spell_bindings: list[int] = field(default_factory=list)
    controls: tuple[Controls, ...] = ()
    gcd_mod: float = 1.0


@dataclass(slots=True)
class ObjCastingData:
    """ECS-style component storing casting, cooldown, and input data for a GameObj."""
    ability_cd_start: list[int] = field(default_factory=list)
    gcd_start: int = -10000
    gcd_mod: float = 1.0
    spell_bindings: list[int] = field(default_factory=list)
    controls: tuple[Controls, ...] = ()
    current_spell_cast: int = Consts.EMPTY_ID
    cast_start_time: int = 0

    @classmethod
    def create_environment(cls) -> 'ObjCastingData':
        return cls(
            ability_cd_start=[],
            gcd_start=-10000,
            gcd_mod=1.0,
            spell_bindings=[Consts.EMPTY_ID] * len(LOADOUT_KEY_TO_INDEX_MAP),
            controls=(),
            current_spell_cast=Consts.EMPTY_ID,
            cast_start_time=0,
        )

    @classmethod
    def create_from_spell(cls, timestamp: int, spell_data: SpellCastingData) -> 'ObjCastingData':
        return cls(
            ability_cd_start=[Consts.EMPTY_TIMESTAMP] * len(spell_data.spell_bindings),
            gcd_start=-10000,
            gcd_mod=spell_data.gcd_mod,
            spell_bindings=list(spell_data.spell_bindings),
            controls=spell_data.controls,
            current_spell_cast=Consts.EMPTY_ID,
            cast_start_time=timestamp,
        )


class CastingSystem:
    """
    Manages casting state, cooldowns, GCDs, input parsing, and ability timelines.
    """
    def __init__(self, spell_data_dct: Dict[int, SpellCastingData]) -> None:
        self.spell_data_dct: Dict[int, SpellCastingData] = spell_data_dct
        self.game_obj_data_dct: Dict[int, ObjCastingData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjCastingData.create_environment()

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, spell_id: int) -> None:
        if spell_id not in self.spell_data_dct or new_obj_id in self.game_obj_data_dct:
            return
        spell_data = self.spell_data_dct[spell_id]
        self.game_obj_data_dct[new_obj_id] = ObjCastingData.create_from_spell(timestamp, spell_data)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    def apply_casting_event(self, timestamp: int, source_id: int, spell_id: int) -> None:
        if spell_id not in self.spell_data_dct:
            return

        spell_data = self.spell_data_dct[spell_id]
        flags = spell_data.flags
        source_data = self.game_obj_data_dct.get(source_id)

        if source_data:
            if flags & CastingBehavior.TRIGGER_GCD:
                source_data.gcd_start = timestamp
            if flags & CastingBehavior.TRIGGER_COOLDOWN:
                if spell_id in source_data.spell_bindings:
                    index = source_data.spell_bindings.index(spell_id)
                    source_data.ability_cd_start[index] = timestamp
            if flags & CastingBehavior.START_CHANNEL:
                source_data.cast_start_time = timestamp
                source_data.current_spell_cast = spell_data.effect_id
            if flags & CastingBehavior.STOP_CHANNEL:
                source_data.cast_start_time = timestamp
                source_data.current_spell_cast = Consts.EMPTY_ID

    # ---- Cooldown & Input Methods ----

    def get_gcd_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        spell_data = self.spell_data_dct.get(spell_id)
        if spell_data is None or not (spell_data.flags & CastingBehavior.TRIGGER_GCD):
            return 1.0

        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return 1.0

        base_gcd = float(getattr(Consts, "BASE_GCD", 0.0))
        gcd_duration = base_gcd * obj_data.gcd_mod
        if gcd_duration <= 0:
            return 1.0

        progress = (current_timestamp - obj_data.gcd_start) / gcd_duration
        return min(1.0, max(0.0, progress))

    def is_gcd_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        return self.get_gcd_progress(obj_id, spell_id, current_timestamp) >= 1.0

    def get_cooldown_progress(self, obj_id: int, spell_id: int, current_timestamp: int) -> float:
        spell_data = self.spell_data_dct.get(spell_id)
        if spell_data is None or not (spell_data.flags & CastingBehavior.TRIGGER_COOLDOWN):
            return 1.0

        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None or spell_id not in obj_data.spell_bindings:
            return 1.0

        index = obj_data.spell_bindings.index(spell_id)
        cd_duration = spell_data.base_cooldown
        if cd_duration <= 0:
            return 1.0

        cd_start = obj_data.ability_cd_start[index]
        progress = (current_timestamp - cd_start) / cd_duration
        return min(1.0, max(0.0, progress))

    def is_cooldown_ready(self, obj_id: int, spell_id: int, current_timestamp: int) -> bool:
        return self.get_cooldown_progress(obj_id, spell_id, current_timestamp) >= 1.0

    def get_spell_ids_for_inputs(self, obj_id: int, hardware_inputs: list[str]) -> Iterable[int]:
        if not hardware_inputs:
            return

        key_presses = InputTranslator.translate_to_keypresses(hardware_inputs)
        if key_presses == KeyPresses.NONE:
            return

        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.spell_bindings:
            return

        for key_flag, index in LOADOUT_KEY_TO_INDEX_MAP.items():
            if key_flag & key_presses:
                if index < len(obj_data.spell_bindings):
                    spell_id = obj_data.spell_bindings[index]
                    if Consts.is_valid_id(spell_id):
                        yield spell_id

    def get_scripted_spells(self, obj_id: int, spawn_timestamp: int) -> Iterable[tuple[int, int, int]]:
        obj_data = self.game_obj_data_dct.get(obj_id)
        if not obj_data or not obj_data.controls or not obj_data.spell_bindings:
            return

        for original_controls in obj_data.controls:
            controls = original_controls.create_copy()
            controls.increase_offset(spawn_timestamp)

            priority = 0
            for key_flag, index in LOADOUT_KEY_TO_INDEX_MAP.items():
                if key_flag in controls.key_presses:
                    if index < len(obj_data.spell_bindings):
                        spell_id = obj_data.spell_bindings[index]
                        if Consts.is_valid_id(spell_id):
                            priority += 1
                            yield spell_id, controls.ingame_time, priority

    # ---- Timeline & Sequence Properties ----

    def get_spell_sequence(self, spell_id: int) -> tuple[int, ...]:
        return self.spell_data_dct[spell_id].spell_sequence

    def get_effect_id(self, spell_id: int) -> int:
        return self.spell_data_dct[spell_id].effect_id

    def has_channel_start(self, spell_id: int) -> bool:
        return bool(self.spell_data_dct[spell_id].flags & CastingBehavior.START_CHANNEL)

    def get_ability_timeline(self, spell_id: int) -> Mapping[int, Union[int, tuple[int, ...]]]:
        return self.spell_data_dct[spell_id].timeline

    def get_tick_timestamps(self, current_timestamp: int, spell_id: int) -> Iterable[int]:
        """Yield timestamps for all ticks occuring during the aura's lifetime. """
        spell_data = self.spell_data_dct[spell_id]
        if spell_data.ticks > 0:
            assert spell_data.duration % spell_data.ticks == 0, f"Non-integer tick interval: duration={spell_data.duration}, ticks={spell_data.ticks}"
            tick_interval = spell_data.duration // spell_data.ticks
            for i in range(1, spell_data.ticks + 1):
                tick_timestamp = current_timestamp + i * tick_interval
                assert isinstance(tick_timestamp, int), f"Non-int tick timestamp: {tick_timestamp}"
                yield tick_timestamp

    def is_aura_active(self, current_timestamp: int, obj_id: int, spell_id: int) -> bool:
        obj_data = self.game_obj_data_dct.get(obj_id)
        if obj_data is None:
            return False
        spell_data = self.spell_data_dct.get(spell_id)
        # Determine if it has surpassed its duration
        if spell_data and current_timestamp > (obj_data.cast_start_time + spell_data.duration):
            return False
        # Ensure spell cast wasn't canceled
        if obj_data.current_spell_cast != self.spell_data_dct[spell_id].effect_id:
            return False
        return True