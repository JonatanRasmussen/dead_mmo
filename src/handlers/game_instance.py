from typing import Dict, List, Tuple, ValuesView
import heapq

from src.models.world_state import WorldState
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.handlers.event_system import EventSystem


class GameInstance:
    def __init__(self) -> None:
        self._state = WorldState()
        self._event_system = EventSystem()

    def setup_game(self, setup_spell_id: int) -> None:
        self._event_system.setup_game(setup_spell_id, self._state)

    def process_frame(self, delta_time: float, player_input: Controls) -> None:
        timestamped_controls = player_input.replace_timestamp(self._state.current_timestamp)
        self._state.advance_timestamp(delta_time)
        self._state.add_player_controls(timestamped_controls)
        self._event_system.find_events_happening_this_frame(self._state)
        self._event_system.process_events_happening_this_frame(self._state)

    def get_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self._state.game_objs.values()

    def simulate_game_in_console(self) -> None:
        setup_spell_id = 300
        self.setup_game(setup_spell_id)
        SIMULATION_DURATION = 6
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of controls
            controls = Controls(start_move_up=True, ability_1=True)
            self.process_frame(1 / UPDATES_PER_SECOND, controls)

