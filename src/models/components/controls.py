from typing import NamedTuple, Tuple

from src.config import Consts


class Controls(NamedTuple):
    """ Keypresses for a given timestamp. Is used to make game objects initiate a spellcast. """
    obj_id: int = Consts.EMPTY_ID
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
    def get_key_for_controls(self) -> Tuple[float, int]:
        return (self.ingame_timestamp, self.obj_id)

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
    def ingame_timestamp(self) -> float:
        return self.timeline_timestamp + self.offset

    @property
    def has_valid_timestamp(self) -> bool:
        return self.timeline_timestamp != Consts.EMPTY_TIMESTAMP

    def replace_timestamp(self, new_timestamp: float) -> 'Controls':
        return self._replace(timeline_timestamp=new_timestamp)

    def increase_offset_and_assign_obj_id(self, new_obj_id: int, additional_offset: float) -> 'Controls':
        updated_obj_id = self.assign_obj_id(new_obj_id)
        return updated_obj_id.increase_offset(additional_offset)

    def assign_obj_id(self, new_obj_id: int) -> 'Controls':
        assert self.obj_id == Consts.EMPTY_ID, f"Controls was assigned new obj_id {new_obj_id} but obj_id is already {self.obj_id}"
        return self._replace(obj_id=new_obj_id)

    def increase_offset(self, additional_offset: float) -> 'Controls':
        assert self.offset == 0.0, "Controls has been offset more than once, is this intentional?"
        new_offset = self.offset + additional_offset
        return self._replace(offset=new_offset)

    def is_happening_now(self, last_visit: float, now: float) -> bool:
        return self.timeline_timestamp > last_visit and self.timeline_timestamp <= now