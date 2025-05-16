from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.models.controls import Controls
from src.models.spell import Spell
from src.handlers.id_gen import IdGen


class ControlsHandler:

    def __init__(self) -> None:
        self._controls: SortedDict[Tuple[float, int], Controls] = SortedDict()

    def get_controls(self, timestamp: float, obj_id: int) -> Controls:
        key: Tuple[float, int] = (timestamp, obj_id)
        assert key in self._controls, f"Controls with (timestamp, obj_id) = {key} does not exist."
        return self._controls.get(key, Controls())

    def get_controls_in_timerange(self, prev_t: float, curr_t: float, min_id: int, max_id: int) -> List[Tuple[float, int, Controls]]:
        start_key = (prev_t, min_id)
        end_key = (curr_t, max_id)
        return [(k[0], k[1], self._controls[k]) for k in self._controls.irange(start_key, end_key)]

    def add_realtime_player_controls(self, obj_id: int, timestamp: float, new_controls: Controls) -> None:
        if IdGen.is_valid_id(obj_id):
            timestamped_controls = new_controls.replace_timestamp(timestamp)
            self.add_controls(obj_id, timestamp, timestamped_controls)

    def add_controls(self, obj_id: int, timestamp: float, new_controls: Controls) -> None:
        key: Tuple[float, int] = (timestamp, obj_id)
        assert IdGen.is_valid_id(obj_id), "Controls for invalid / empty GameObj cannot be added."
        assert new_controls.has_valid_timestamp, "Controls has invalid / uninitialized timestamp."
        assert key not in self._controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self._controls[key] = new_controls

    def try_add_controls_for_newly_spawned_obj(self, obj_id: int, spell: Spell):
        if spell.obj_controls is not None:
            for controls in spell.obj_controls:
                self.add_controls(obj_id, controls.timestamp, controls)