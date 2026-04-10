from src.models.components.controls import Controls
from typing import ValuesView

from .models.data import Spell
from .models.components import Controls, GameObj, KeyPresses
from .models.events.finalized_event import FinalizedEvent
from .pygame_renderer import PygameRenderer
from .ui_manager import UiManager
from .world_state import WorldState

class IngameLoop:
    TEST_SETUP_SPELL_IDS: list[int] = [300]

    def __init__(self) -> None:
        self._state: WorldState = WorldState()
        self._rendering_framework = PygameRenderer()
        self._ui_manager = UiManager()

    def simulate_game_in_console(self, setup_spell_ids: list[int]) -> None:
        ingame_time = 0
        self._state.process_setup_events(ingame_time, setup_spell_ids)
        SIMULATION_DURATION_MS = 6000
        UPDATES_PER_SECOND = 50
        FRAME_DURATION_MS = 1000 // UPDATES_PER_SECOND
        num_iterations = SIMULATION_DURATION_MS // FRAME_DURATION_MS
        for _ in range(num_iterations):
            simulated_player_input = Controls(key_presses=KeyPresses.START_MOVE_UP | KeyPresses.ABILITY_1)
            ingame_time += FRAME_DURATION_MS
            player_inputs_this_frame: list[Controls] = [simulated_player_input]
            self._state.process_frame(player_inputs_this_frame, ingame_time)

    def play_game_in_pygame(self, setup_spell_ids: list[int]) -> None:
        self._rendering_framework.launch_rendering_framework()
        ingame_time = 0
        cached_time = self._rendering_framework.get_current_time()
        self._state.process_setup_events(ingame_time, setup_spell_ids)
        while self._rendering_framework.is_running():

            # Fetch player input and send it to server
            serialized_input = self._rendering_framework.fetch_player_input()
            current_player_input = Controls.deserialize(serialized_input)

            # Update time
            current_time = self._rendering_framework.get_current_time()
            rounding_error = 0.0
            exact_delta_time_ms = (current_time - cached_time) * 1000.0 + rounding_error
            rounded_delta_time_ms = int(round(exact_delta_time_ms))  # smallest in-game time unit is 1ms
            rounding_error = exact_delta_time_ms - rounded_delta_time_ms
            if rounded_delta_time_ms < 1:
                rounding_error += exact_delta_time_ms - 1
                rounded_delta_time_ms = 1
            cached_time = current_time

            # Simulate next frame
            ingame_time += rounded_delta_time_ms
            player_inputs_this_frame: list[Controls] = [current_player_input]
            self._state.process_frame(player_inputs_this_frame, ingame_time)

            # Render this frame
            self._rendering_framework.begin_frame()
            events_view: ValuesView[FinalizedEvent] = self._state.view_all_frame_events(ingame_time)
            for event in events_view:
                self._apply_event(event)
            game_objs_view: ValuesView[GameObj] = self._state.view_game_objs
            for game_obj in game_objs_view:
                self._render_game_obj(game_obj)
            self._render_frame_actions()
            self._rendering_framework.end_frame()

        # Cleanup when exiting game
        self._rendering_framework.terminate_rendering_framework()

    def _apply_event(self, event: FinalizedEvent) -> None:
        spell: Spell = self._state.spell_database.get_spell(event.spell_id)

        if spell.should_play_audio and event.outcome_is_valid:
            self._rendering_framework.play_sound(spell.audio_name)

        if spell.should_play_animation and event.outcome_is_valid:
            pos = (0.0, 0.0)  # Replace with real effect position later
            self._rendering_framework.play_animation(
                pos_xy=pos,
                scale=spell.animation_scale,
                asset_name=spell.animation_name
            )

    def _render_game_obj(self, game_obj: GameObj) -> None:
        if game_obj.is_visible:
            self._rendering_framework.draw_blinking_circle(
                pos_xy=(game_obj.pos.x, game_obj.pos.y),
                scale=game_obj.size,
                color_rgb=game_obj.color,
                time_ms=self._rendering_framework.get_current_time(),
                asset_name=game_obj.sprite_name
            )

    def _render_frame_actions(self) -> None:
        for rend_act in self._ui_manager.get_render_actions():
            if rend_act.is_type_circle():
                scale = rend_act.convert_scale_xy_to_scale()
                self._rendering_framework.draw_circle(
                    rend_act.pos_xy,
                    scale,
                    rend_act.color_rgb,
                    rend_act.asset_name
                )

            elif rend_act.is_type_rectangle():
                self._rendering_framework.draw_rectangle(
                    rend_act.pos_xy,
                    rend_act.scale_xy,
                    rend_act.color_rgb,
                    rend_act.asset_name
                )

            elif rend_act.is_type_animation():
                scale = rend_act.convert_scale_xy_to_scale()
                self._rendering_framework.play_animation(
                    rend_act.pos_xy,
                    scale,
                    rend_act.asset_name
                )

            elif rend_act.is_type_text():
                font_size = rend_act.convert_scale_xy_to_font_size()
                self._rendering_framework.display_text(
                    rend_act.pos_xy,
                    font_size,
                    rend_act.color_rgb,
                    rend_act.text_to_display
                )

            elif rend_act.is_type_audio():
                self._rendering_framework.play_sound(rend_act.asset_name)

        self._ui_manager.clear_current_frame_event_cache()