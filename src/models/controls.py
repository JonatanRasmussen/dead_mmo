from typing import NamedTuple


class Controls(NamedTuple):
    """ Keypresses for a given timestamp. Is used to make game objects initiate a spellcast. """
    timestamp: float = 0.0

    start_move_up: bool = False
    stop_move_up: bool = False
    start_move_left: bool = False
    stop_move_left: bool = False
    start_move_down: bool = False
    stop_move_down: bool = False
    start_move_right: bool = False
    stop_move_right: bool = False

    next_target: bool = False
    ability_1: bool = False
    ability_2: bool = False
    ability_3: bool = False
    ability_4: bool = False

    def replace_timestamp(self, new_timestamp: float) -> 'Controls':
        return self._replace(timestamp=new_timestamp)

    def is_happening_now(self, last_visit: float, now: float) -> bool:
        return self.timestamp > last_visit and self.timestamp <= now
