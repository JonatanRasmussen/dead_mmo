from typing import List, ValuesView
import math

from src.models.components import Controls, FinalizedEvent, GameObj
from src.models.handlers import EventLog
from src.models.managers.world_state import WorldState


class GameInstance:
    def __init__(self, environment_setup_id: int) -> None:
        self._state: WorldState = WorldState(environment_setup_id)
        self._event_frame_logs: list[EventLog] = []
        self._ingame_time: int = 0
        self._rounding_error: float = 0.0

    @property
    def ingame_time(self) -> int:
        return self._ingame_time

    @property
    def view_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self._state.view_game_objs

    @property
    def view_all_events_this_frame(self) -> ValuesView[FinalizedEvent]:
        assert len(self._event_frame_logs) > 0
        assert self.ingame_time == self._event_frame_logs[-1].frame_end
        return self._event_frame_logs[-1].view_all_events

    @property
    def rounding_error(self) -> float:
        return self._rounding_error

    def convert_delta_time_to_int_in_ms(self, delta_time: float) -> int:
        milliseconds = delta_time * 1000.0 + self._rounding_error
        rounded_ms = int(round(milliseconds))
        self._rounding_error = milliseconds - rounded_ms  #track rounding to avoid game speedup
        if rounded_ms < 1:  #avoid zero-frame stalls
            self._rounding_error += milliseconds - 1
            return 1
        return rounded_ms

    def process_next_frame(self, delta_time: int, player_input: Controls) -> None:
        frame_start = self.ingame_time
        self._ingame_time += delta_time
        frame_end = self.ingame_time
        self._state.add_realtime_player_controls(player_input, frame_end)
        event_log = self._state.process_frame(frame_start, frame_end)
        self._event_frame_logs.append(event_log)

    @staticmethod
    def simulate_game_in_console(setup_spell_id: int) -> None:
        game_instance = GameInstance(setup_spell_id)
        SIMULATION_DURATION_MS = 6000
        UPDATES_PER_SECOND = 50
        FRAME_DURATION_MS = 1000 // UPDATES_PER_SECOND
        num_iterations = SIMULATION_DURATION_MS // FRAME_DURATION_MS
        for _ in range(num_iterations):
            # example of controls
            controls = Controls(start_move_up=True, ability_1=True)
            game_instance.process_next_frame(FRAME_DURATION_MS, controls)