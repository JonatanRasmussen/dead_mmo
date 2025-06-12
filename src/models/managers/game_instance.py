from typing import List, ValuesView

from src.models.components import Controls, FinalizedEvent, GameObj
from src.models.services import EventLog
from src.models.managers.world_state import WorldState


class GameInstance:
    def __init__(self, environment_setup_id: int) -> None:
        self._state: WorldState = WorldState(environment_setup_id)
        self._event_frame_logs: List[EventLog] = []
        self._ingame_time: float = 0.0

    @property
    def ingame_time(self) -> float:
        return self._ingame_time

    @property
    def view_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self._state.view_game_objs

    @property
    def view_all_events_this_frame(self) -> ValuesView[FinalizedEvent]:
        assert len(self._event_frame_logs) > 0
        assert self.ingame_time == self._event_frame_logs[-1].frame_end
        return self._event_frame_logs[-1].view_all_events

    def process_next_frame(self, delta_time: float, player_input: Controls) -> None:
        frame_start = self.ingame_time
        self.advance_ingame_time(delta_time)
        frame_end = self.ingame_time
        frame_middle = frame_start + (frame_end - frame_start) / 2
        self._state.add_realtime_player_controls(player_input, frame_middle)
        event_log = self._state.process_frame(frame_start, frame_end)
        self._event_frame_logs.append(event_log)

    @staticmethod
    def simulate_game_in_console(setup_spell_id: int) -> None:
        game_instance = GameInstance(setup_spell_id)
        SIMULATION_DURATION = 6
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of controls
            controls = Controls(start_move_up=True, ability_1=True)
            game_instance.process_next_frame(1 / UPDATES_PER_SECOND, controls)

    def advance_ingame_time(self, delta_time: float) -> None:
        self._ingame_time += delta_time
