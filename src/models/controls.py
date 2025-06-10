from typing import NamedTuple

from src.config import Consts


class Controls(NamedTuple):
    """ Keypresses for a given timestamp. Is used to make game objects initiate a spellcast. """
    timeline_timestamp: float = Consts.EMPTY_TIMESTAMP
    offset: float = 0.0

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
    def ingame_timestamp(self) -> float:
        return self.timeline_timestamp + self.offset

    @property
    def has_valid_timestamp(self) -> bool:
        return self.timeline_timestamp != Consts.EMPTY_TIMESTAMP

    def replace_timestamp(self, new_timestamp: float) -> 'Controls':
        return self._replace(timeline_timestamp=new_timestamp)

    def increase_offset(self, additional_offset: float) -> 'Controls':
        assert self.offset == 0.0, "Controls has been offset more than once, is this intentional?"
        new_offset = self.offset + additional_offset
        return self._replace(offset=new_offset)

    def is_happening_now(self, last_visit: float, now: float) -> bool:
        return self.timeline_timestamp > last_visit and self.timeline_timestamp <= now