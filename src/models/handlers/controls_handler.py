from sortedcontainers import SortedDict  # type: ignore
from typing import List, Tuple, Iterable, Optional

from src.config import Consts
from src.models.components import Controls, GameObj, Spell


class ControlsHandler:

    def __init__(self) -> None:
        self._controls: SortedDict[tuple[int, int], Controls] = SortedDict()

    """def get_controls_in_timerange(self, frame_start: int, frame_end: int) -> Iterable[tuple[int, int, Controls]]:
        start_key = (frame_start, Consts.MIN_ID)
        end_key = (frame_end, Consts.MAX_ID)
        yield from ((k[0], k[1], self._controls[k]) for k in self._controls.irange(start_key, end_key, inclusive=(False, True)))"""

    def get_controls_in_timerange(self, frame_start: int, frame_end: int) -> Iterable[tuple[int, int, Controls]]:
        for (timestamp, obj_id), controls in self._controls.items():
            if frame_start < timestamp <= frame_end:
                yield (timestamp, obj_id, controls)

    def add_realtime_player_controls(self, new_controls: Controls, timestamp: int, obj_id: int) -> None:
        if Consts.is_valid_id(obj_id) and not new_controls.is_empty:
            assert timestamp != 0, "timestamp should not be 0"
            assert not new_controls.is_empty, f"{obj_id} has empty controls"
            new_controls.timeline_timestamp = timestamp
            new_controls.obj_id = obj_id
            self._add_controls(new_controls)

    def add_controls_for_newly_spawned_obj(self, game_obj: Optional[GameObj], spell: Spell) -> None:
        if game_obj is not None and spell.obj_controls is not None:
            for controls in spell.copy_obj_controls:
                controls.obj_id = game_obj.obj_id
                controls.increase_offset(game_obj.cds.spawn_timestamp)
                assert not controls.is_empty, f"{game_obj.obj_id} has empty controls"
                self._add_controls(controls)

    def _add_controls(self, new_controls: Controls) -> None:
        key: tuple[int, int] = new_controls.get_key_for_controls
        assert Consts.is_valid_id(new_controls.obj_id), "Controls for invalid / empty GameObj cannot be added."
        assert new_controls.has_valid_timestamp, "Controls has invalid / uninitialized timestamp."
        assert not new_controls.is_empty, f"{new_controls.obj_id} has empty controls"
        assert key not in self._controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self._controls[key] = new_controls
