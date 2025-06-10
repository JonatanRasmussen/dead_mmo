from sortedcontainers import SortedDict  # type: ignore
from typing import List, Tuple

from src.config import Consts
from src.models import Controls, GameObj, Spell, UpcomingEvent


class ControlsHandler:

    def __init__(self) -> None:
        self._controls: SortedDict[Tuple[float, int], Controls] = SortedDict()

    def get_controls_in_timerange(self, prev_t: float, curr_t: float) -> List[Tuple[float, int, Controls]]:
        start_key = (prev_t, Consts.MIN_ID)
        end_key = (curr_t, Consts.MAX_ID)
        return [(k[0], k[1], self._controls[k]) for k in self._controls.irange(start_key, end_key)]

    def add_realtime_player_controls(self, obj_id: int, timestamp: float, new_controls: Controls) -> None:
        if Consts.is_valid_id(obj_id):
            realtime_controls = new_controls.replace_timestamp(timestamp)
            self.add_controls(obj_id, realtime_controls)

    def add_controls(self, obj_id: int, new_controls: Controls) -> None:
        key: Tuple[float, int] = (new_controls.ingame_timestamp, obj_id)
        assert Consts.is_valid_id(obj_id), "Controls for invalid / empty GameObj cannot be added."
        assert new_controls.has_valid_timestamp, "Controls has invalid / uninitialized timestamp."
        assert key not in self._controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self._controls[key] = new_controls

    def add_controls_for_newly_spawned_obj(self, game_obj: GameObj, spell: Spell) -> None:
        if spell.obj_controls is not None:
            for controls in spell.obj_controls:
                offset_controls = controls.increase_offset(game_obj.spawn_timestamp)
                self.add_controls(game_obj.obj_id, offset_controls)