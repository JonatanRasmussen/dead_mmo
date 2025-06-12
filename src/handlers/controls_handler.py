from sortedcontainers import SortedDict  # type: ignore
from typing import List, Tuple, Iterable

from src.config import Consts
from src.models import Controls, GameObj, Spell, UpcomingEvent


class ControlsHandler:

    def __init__(self) -> None:
        self._controls: SortedDict[Tuple[float, int], Controls] = SortedDict()

    def get_controls_in_timerange(self, frame_start: float, frame_end: float) -> Iterable[Tuple[float, int, Controls]]:
        start_key = (frame_start, Consts.MIN_ID)
        end_key = (frame_end, Consts.MAX_ID)
        yield from ((k[0], k[1], self._controls[k]) for k in self._controls.irange(start_key, end_key))

    def add_realtime_player_controls(self, obj_id: int, frame_middle: float, new_controls: Controls) -> None:
        if Consts.is_valid_id(obj_id) and not new_controls.is_empty:
            assert new_controls.offset == 0.0, "Realtime controls should not have any offset."
            realtime_controls = new_controls.replace_timestamp(frame_middle)
            realtime_player_controls = realtime_controls.assign_obj_id(obj_id)
            assert not realtime_player_controls.is_empty, f"{obj_id} has empty controls"
            self._add_controls(realtime_player_controls)

    def add_controls_for_newly_spawned_obj(self, game_obj: GameObj, spell: Spell) -> None:
        if spell.obj_controls is not None:
            for controls in spell.obj_controls:
                offset_controls = controls.increase_offset_and_assign_obj_id(game_obj.obj_id, game_obj.spawn_timestamp)
                assert not offset_controls.is_empty, f"{game_obj.obj_id} has empty controls"
                self._add_controls(offset_controls)

    def _add_controls(self, new_controls: Controls) -> None:
        key: Tuple[float, int] = new_controls.get_key_for_controls
        assert Consts.is_valid_id(new_controls.obj_id), "Controls for invalid / empty GameObj cannot be added."
        assert new_controls.has_valid_timestamp, "Controls has invalid / uninitialized timestamp."
        assert not new_controls.is_empty, f"{new_controls.obj_id} has empty controls"
        assert key not in self._controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self._controls[key] = new_controls
