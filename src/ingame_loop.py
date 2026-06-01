from typing import ValuesView

from src.models.events.upcoming_event import UpcomingEvent

from .models.data import Spell
from .models.components import Controls, GameObj, KeyPresses
from .pygame_renderer import PygameRenderer
from .ui_manager import UiManager
from .world_state import WorldState
from ._sim_validation import SimValidation
from ._input_translator import InputTranslator
from src.consts import HardwareInputConsts
from src.consts import LevelSetupConsts


class IngameLoop:
    def __init__(self) -> None:
        self._state: WorldState = WorldState()
        self._rendering_framework = PygameRenderer()
        self._ui_manager = UiManager()

    @staticmethod
    def temp_testing_delete_later() -> None:
        IngameLoop().simulate_game_in_console(
            LevelSetupConsts.TEST_SETUP_SPELL_IDS,
            LevelSetupConsts.SCRIPTED_PLAYER_INPUT_FOR_TESTING
        )
        IngameLoop().play_game_in_pygame(
            LevelSetupConsts.TEST_SETUP_SPELL_IDS,
            LevelSetupConsts.SCRIPTED_PLAYER_INPUT_FOR_TESTING
        )

    @staticmethod
    def temp_main_delete_later() -> None:
        IngameLoop().simulate_game_in_console(
            LevelSetupConsts.TEST_SETUP_SPELL_IDS,
            LevelSetupConsts.SCRIPTED_PLAYER_INPUT_FOR_TESTING
        )
        IngameLoop().play_game_in_pygame(
            LevelSetupConsts.TEST_SETUP_SPELL_IDS
        )

    def simulate_game_in_console(self, setup_spell_ids: list[int], scripted_player_input: dict[int, list[str]]) -> None:
        ingame_time = 0
        self._state.process_setup_events(ingame_time, setup_spell_ids)

        SIMULATION_DURATION_MS = 10000
        UPDATES_PER_SECOND = 50
        FRAME_DURATION_MS = 1000 // UPDATES_PER_SECOND
        number_of_iterations = SIMULATION_DURATION_MS // FRAME_DURATION_MS

        player_inputs_this_frame: list[KeyPresses] = []

        for _ in range(number_of_iterations):
            ingame_time += FRAME_DURATION_MS

            player_inputs_this_frame.clear()
            for timestamp, inputs in scripted_player_input.items():
                if (ingame_time - FRAME_DURATION_MS) < timestamp <= ingame_time:
                    keypresses = InputTranslator.translate_to_keypresses(inputs)
                    player_inputs_this_frame.append(keypresses)
            self._state.process_frame(player_inputs_this_frame, ingame_time)

        SimValidation.run_snapshot_test(self._state, snapshot_name=str(setup_spell_ids))

    def play_game_in_pygame(self, setup_spell_ids: list[int], scripted_player_input: dict[int, list[str]] | None = None) -> None:
        self._rendering_framework.launch_rendering_framework()
        ingame_time = 0
        cached_time = self._rendering_framework.get_current_time()
        self._state.process_setup_events(ingame_time, setup_spell_ids)
        player_inputs_this_frame: list[KeyPresses] = []
        while self._rendering_framework.is_running():
            # Update time
            current_time = self._rendering_framework.get_current_time()
            rounding_error = 0.0
            exact_delta_time_ms = (current_time - cached_time) * 1000.0 + rounding_error
            rounded_delta_time_ms = int(round(exact_delta_time_ms))  # round to smallest allowed in-game time unit
            rounding_error = exact_delta_time_ms - rounded_delta_time_ms
            if rounded_delta_time_ms < 1:
                rounding_error += exact_delta_time_ms - 1
                rounded_delta_time_ms = 1
            cached_time = current_time
            ingame_time += rounded_delta_time_ms

            # Fetch player input and send it to server
            player_inputs_this_frame.clear()
            if scripted_player_input is None:
                # Player is controlling the game
                current_inputs: list[str] = self._rendering_framework.fetch_player_input()
                if current_inputs:
                    keypresses = InputTranslator.translate_to_keypresses(current_inputs)
                    player_inputs_this_frame.append(keypresses)
            else:
                # Player is NOT controlling game; scripted player input is used instead (for testing purposes)
                _ = self._rendering_framework.fetch_player_input()  # Only called to allow Escape keypress to close game
                for timestamp, inputs in scripted_player_input.items():
                    if (ingame_time - rounded_delta_time_ms) < timestamp <= ingame_time:
                        keypresses = InputTranslator.translate_to_keypresses(inputs)
                        player_inputs_this_frame.append(keypresses)

            # Simulate next frame
            self._state.process_frame(player_inputs_this_frame, ingame_time)

            # Render this frame
            self._rendering_framework.begin_frame()
            events_view: ValuesView[UpcomingEvent] = self._state.view_event_logs[ingame_time].view_all_events
            for event in events_view:
                self._apply_event(event)
            game_objs_view: ValuesView[GameObj] = self._state.view_game_objs
            for game_obj in game_objs_view:
                self._render_game_obj(game_obj)
            self._render_frame_actions()
            self._rendering_framework.end_frame()

        # Cleanup when exiting game
        self._rendering_framework.terminate_rendering_framework()

    def _apply_event(self, event: UpcomingEvent) -> None:
        spell: Spell = self._state.spell_database.get_spell(event.spell_id)

        if spell.should_play_audio and event.outcome_is_valid:
            self._rendering_framework.play_sound(spell.audio_name)

        if spell.should_play_animation and event.outcome_is_valid:
            pos = (0.0, 0.0)  # Replace with real effect position later
            self._rendering_framework.play_animation(pos_xy=pos, scale=spell.animation_scale, asset_name=spell.animation_name)

    def _render_game_obj(self, game_obj: GameObj) -> None:
        if game_obj.is_visible:
            x, y = game_obj.get_position_xy()
            self._rendering_framework.draw_blinking_circle(
                pos_xy=(x, y),
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