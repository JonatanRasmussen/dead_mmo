from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.models.controls import Controls


class ControlsHandler:

    def __init__(self) -> None:
        self._controls: SortedDict[Tuple[float, int], Controls] = SortedDict()

    def get_controls(self, timestamp: float, obj_id: int) -> Controls:
        key: Tuple[float, int] = (timestamp, obj_id)
        assert key in self._controls, f"Controls with (timestamp, obj_id) = {key} does not exist."
        return self._controls.get(key, Controls())

    def get_controls_in_timerange(self, prev_t: float, curr_t: float) -> List[Tuple[float, int, Controls]]:
        start_key = (prev_t, -1_000_000)
        end_key = (curr_t, 1_000_000)
        return [(k[0], k[1], self._controls[k]) for k in self._controls.irange(start_key, end_key)]

    def add_controls(self, obj_id: int, timestamp: float, new_controls: Controls) -> None:
        key: Tuple[float, int] = (timestamp, obj_id)
        assert new_controls.has_valid_timestamp, "Controls has invalid / uninitialized timestamp."
        assert key not in self._controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self._controls[key] = new_controls
