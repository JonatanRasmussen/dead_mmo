from typing import Protocol, ValuesView
from typing_extensions import override
from src.models.components import Controls
from src.models.components import GameObj
from src.models.managers.combat_instance import CombatInstance
from src.models.events.finalized_event import FinalizedEvent

class BackendServer:
    def __init__(self) -> None:
        self.game_instance: CombatInstance = CombatInstance(setup_spell_ids=[300])
        self._current_player_input = Controls()
        self._temporary_frame_events_fix_later: list[tuple[int, int, int, int, float, bool]] = []
        self._temporary_frame_event_has_not_been_filled: bool = True
        self._temporary_updated_game_objs_fix_later: list[tuple[tuple[float, float], float, tuple[int, int, int], str, bool]] = []
        self._temporary_updated_game_objs_has_not_been_filled: bool = True

    def send_player_input(self, serialized_input: str) -> None:
        self._current_player_input = Controls.deserialize(serialized_input)

    def simulate_next_frame(self, elapsed_time: float) -> None:
        delta_time_in_ms = self.game_instance.convert_delta_time_to_int_in_ms(elapsed_time)
        self.game_instance.process_next_frame(delta_time_in_ms, self._current_player_input)

    def request_updated_event(self) -> tuple[int, int, int, int, float, bool] | None:
        if len(self._temporary_frame_events_fix_later) == 0 and self._temporary_frame_event_has_not_been_filled:  # If buffer is empty, refill it from this frame's events
            self._temporary_frame_event_has_not_been_filled = False
            events_view: ValuesView[FinalizedEvent] = self.game_instance.view_all_events_this_frame  # ValuesView[FinalizedEvent]
            self._temporary_frame_events_fix_later = [  # Convert ValuesView -> list of tuples
                (
                    event.timestamp,
                    event.source_id,
                    event.spell_id,
                    event.target_id,
                    event.spell_modifier,
                    event.outcome_is_valid
                )
                for event in events_view
            ]
        if len(self._temporary_frame_events_fix_later) == 0:
            self._temporary_frame_event_has_not_been_filled = True
            return None
        return self._temporary_frame_events_fix_later.pop(0)  # Pop first element (Queue behavior)

    def request_updated_obj(self) -> tuple[tuple[float, float], float, tuple[int, int, int], str | None, bool] | None:
        if len(self._temporary_updated_game_objs_fix_later) == 0 and self._temporary_updated_game_objs_has_not_been_filled:
            # If buffer is empty, refill it from this frame's objects
            self._temporary_updated_game_objs_has_not_been_filled = False
            game_objs_view: ValuesView[GameObj] = self.game_instance.view_all_game_objs_to_draw
            self._temporary_updated_game_objs_fix_later = [
                (
                    (game_obj.pos.x, game_obj.pos.y),
                    game_obj.size,
                    game_obj.color,
                    game_obj.sprite_name,
                    game_obj.is_visible
                )
                for game_obj in game_objs_view
            ]
        if len(self._temporary_updated_game_objs_fix_later) == 0:
            self._temporary_updated_game_objs_has_not_been_filled = True
            return None
        return self._temporary_updated_game_objs_fix_later.pop(0)