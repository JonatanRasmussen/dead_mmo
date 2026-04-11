import json
from dataclasses import dataclass

from src.settings import Consts
from src.models.utils.copy_utils import CopyTools
from .key_presses import KeyPresses

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