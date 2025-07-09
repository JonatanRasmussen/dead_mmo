from dataclasses import dataclass

from src.config import Consts
from src.models.utils.copy_utils import CopyTools

@dataclass(slots=True)
class Controls:
    """ Keypresses for a given timestamp. Is used to make game objects initiate a spellcast. """
    obj_id: int = Consts.EMPTY_ID
    timeline_timestamp: int = Consts.EMPTY_TIMESTAMP
    _offset: int = 0

    start_move_up: bool = False
    stop_move_up: bool = False
    start_move_left: bool = False
    stop_move_left: bool = False
    start_move_down: bool = False
    stop_move_down: bool = False
    start_move_right: bool = False
    stop_move_right: bool = False

    swap_target: bool = False
    ability_1: bool = False
    ability_2: bool = False
    ability_3: bool = False
    ability_4: bool = False

    @property
    def get_key_for_controls(self) -> tuple[int, int]:
        return (self.ingame_time, self.obj_id)

    @property
    def is_empty(self) -> bool:
        return not any((
            self.start_move_up,
            self.stop_move_up,
            self.start_move_left,
            self.stop_move_left,
            self.start_move_down,
            self.stop_move_down,
            self.start_move_right,
            self.stop_move_right,
            self.swap_target,
            self.ability_1,
            self.ability_2,
            self.ability_3,
            self.ability_4,
        ))

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
