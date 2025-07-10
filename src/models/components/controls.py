from dataclasses import dataclass

from src.config import Consts
from src.models.utils.copy_utils import CopyTools
from .key_presses import KeyPresses

@dataclass(slots=True)
class Controls:
    """ Keypresses for a given timestamp. Used to make game objects initiate a spellcast. """
    obj_id: int = Consts.EMPTY_ID
    timeline_timestamp: int = Consts.EMPTY_TIMESTAMP
    _offset: int = 0

    key_presses: KeyPresses = KeyPresses.NONE

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