from typing import Protocol, List, ValuesView
from src.game_loop import IBackendAccess
from src.models.components import Controls, GameObj
from src.models.events import FinalizedEvent
from src.models.managers.combat_instance import CombatInstance

class LocalBackend(IBackendAccess):
    def __init__(self) -> None:
        self.game_instance = CombatInstance(setup_spell_ids=[300])
        self._current_player_input: Controls = Controls()

    def send_player_input(self, serialized_input: str) -> None:
        self._current_player_input = Controls.deserialize(serialized_input)

    def request_updated_events(self, elapsed_time: float) -> list[str]:
        delta_time_in_ms = self.game_instance.convert_delta_time_to_int_in_ms(elapsed_time)
        self.game_instance.process_next_frame(delta_time_in_ms, self._current_player_input)
        serialized_event_lst: list[str] = []
        for f_event in self.game_instance.view_all_events_this_frame:
            serialized_event_lst.append(f_event.serialize())
        return serialized_event_lst

    def request_serialized_game_state(self) -> list[str]:
        serialized_obj_lst: list[str] = []
        for game_obj in self.game_instance.view_all_game_objs_to_draw:
            serialized_obj_lst.append(game_obj.serialize())
        return serialized_obj_lst
