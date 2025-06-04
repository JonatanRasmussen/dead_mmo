from typing import List, ValuesView

from src.models.controls import Controls
from src.models.event import FinalizedEvent
from src.models.game_obj import GameObj
from src.controllers.world_state import WorldState
from src.controllers.event_frame import EventFrame
from src.handlers.event_log import EventLog


class GameInstance:
    def __init__(self) -> None:
        self._state: WorldState = WorldState()
        self._event_frame_logs: List[EventLog] = []

    @property
    def ingame_time(self) -> float:
        return self._state.get_ingame_time

    @property
    def event_log_for_current_frame(self) -> EventLog:
        assert len(self._event_frame_logs) > 0
        assert self.ingame_time == self._event_frame_logs[-1].frame_end
        return self._event_frame_logs[-1]

    @property
    def view_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self._state.view_game_objs

    @property
    def view_all_events_this_frame(self) -> ValuesView[FinalizedEvent]:
        return self.event_log_for_current_frame.view_all_events

    def setup_game(self, setup_spell_id: int) -> None:
        self._state.initialize_environment(setup_spell_id)

    def process_next_frame(self, delta_time: float, player_input: Controls) -> None:
        frame_start = self.ingame_time
        self._state.advance_ingame_time(delta_time)
        frame_end = self.ingame_time
        self._state.add_player_controls(player_input)
        event_log = EventFrame.update_state(frame_start, frame_end, self._state)
        self._event_frame_logs.append(event_log)

    def simulate_game_in_console(self) -> None:
        setup_spell_id = 300
        self.setup_game(setup_spell_id)
        SIMULATION_DURATION = 6
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of controls
            controls = Controls(start_move_up=True, ability_1=True)
            self.process_next_frame(1 / UPDATES_PER_SECOND, controls)