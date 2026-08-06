from src.settings import Consts
from src.utils.copy_utils import CopyTools
from enum import IntFlag, auto
from typing import Iterable
from dataclasses import dataclass, field
import json
from src.settings import HardwareInputConsts


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
    ability_cds: list[int] = field(default_factory=lambda: [Consts.EMPTY_TIMESTAMP] * len(LOADOUT_KEY_TO_INDEX_MAP))
    gcd_start: int = -1_000

    @classmethod
    def deserialize(cls, data: str) -> 'Loadout':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            spawn_timestamp=d["ts"],
            spell_ids=d["ids"],
            ability_cds=d["cds"],
            gcd_start=d["gcd"]
        )
    def serialize(self) -> str:
        return json.dumps({
            "ts": self.spawn_timestamp,
            "ids": self.spell_ids,
            "cds": self.ability_cds,
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