from typing import Dict, List, Tuple, ValuesView
import heapq

from src.controller.world_state import WorldState
from src.models.controls import Controls
from src.models.game_obj import GameObj


class GameInstance:
    def __init__(self) -> None:
        self._state = WorldState()

    def setup_game(self, setup_spell_id: int) -> None:
        self._state.initialize_environment(setup_spell_id)

    def process_frame(self, delta_time: float, player_input: Controls) -> None:
        self._state.process_frame(delta_time, player_input)

    def get_all_game_objs_to_draw(self) -> ValuesView[GameObj]:
        return self._state.all_game_objs

    def simulate_game_in_console(self) -> None:
        setup_spell_id = 300
        self.setup_game(setup_spell_id)
        SIMULATION_DURATION = 6
        UPDATES_PER_SECOND = 2
        for _ in range(0, SIMULATION_DURATION * UPDATES_PER_SECOND):
            # example of controls
            controls = Controls(start_move_up=True, ability_1=True)
            self.process_frame(1 / UPDATES_PER_SECOND, controls)

