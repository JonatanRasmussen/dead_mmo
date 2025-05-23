from typing import Dict, List, Tuple, ValuesView
import heapq

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.controllers.world_state import WorldState
from src.controllers.event_frame import EventFrame


class GameInstance:
    def __init__(self) -> None:
        self.event_frames: Dict[float, EventFrame] = {}
        self._most_recent_frame: EventFrame = EventFrame(0.0, 0.0, WorldState())

    @property
    def state(self) -> WorldState:
        return self._most_recent_frame.state

    @property
    def ingame_time(self) -> float:
        return self._most_recent_frame.frame_end

    @property
    def view_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self.state.view_game_objs

    def setup_game(self, setup_spell_id: int) -> None:
        self.state.initialize_environment(setup_spell_id)

    def next_frame(self, delta_time: float, player_input: Controls) -> None:
        new_frame_start = self._most_recent_frame.frame_end
        new_frame_end = new_frame_start + delta_time
        frame = EventFrame(new_frame_start, new_frame_end, self.state)
        frame.add_player_input(player_input)
        frame.process_frame()
        self.event_frames[frame.frame_start] = frame
        self._most_recent_frame = frame

    def simulate_game_in_console(self) -> None:
        setup_spell_id = 300
        self.setup_game(setup_spell_id)
        SIMULATION_DURATION = 6
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of controls
            controls = Controls(start_move_up=True, ability_1=True)
            self.next_frame(1 / UPDATES_PER_SECOND, controls)