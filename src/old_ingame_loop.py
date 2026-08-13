from typing import ValuesView

from .pygame_renderer import PygameRenderer
from .ui_manager import UiManager
from src.world_state.old_world_state import GameObj, Spell, OldWorldState


class OldIngameLoop:

    @staticmethod
    def play_game_in_pygame(setup_spell_ids: list[int], scripted_player_input: dict[int, list[str]] | None = None) -> None:

        # Initialization
        rendering_framework = PygameRenderer()
        rendering_framework.launch_rendering_framework()
        ingame_time = 0
        rounding_error = 0.0
        cached_time = rendering_framework.get_current_time()
        world_state = OldWorldState()
        world_state.process_setup_events(ingame_time, setup_spell_ids)
        ui_manager = UiManager()

        player_inputs_this_frame: list[str] = []
        while rendering_framework.is_running():
            # Update time (and because smallest in-game timeunit is 1ms, ensure rounding error stays +/- 1ms throughout the game)
            current_time = rendering_framework.get_current_time()
            exact_delta_time_ms = (current_time - cached_time) * 1000.0 + rounding_error
            rounded_delta_time_ms = int(round(exact_delta_time_ms))  # round to smallest allowed in-game time unit
            rounding_error = exact_delta_time_ms - rounded_delta_time_ms
            if rounded_delta_time_ms < 1:
                rounding_error += exact_delta_time_ms - 1
                rounded_delta_time_ms = 1
            cached_time = current_time
            ingame_time += rounded_delta_time_ms

            player_inputs_this_frame.clear()
            if scripted_player_input is None:
                current_inputs: list[str] = rendering_framework.fetch_player_input()
                if current_inputs:
                    player_inputs_this_frame.extend(current_inputs)
            else:
                # Player is NOT controlling game; scripted player input is used instead (for testing purposes)
                _ = rendering_framework.fetch_player_input()  # Only called to allow Escape keypress to close game
                for timestamp, inputs in scripted_player_input.items():
                    if (ingame_time - rounded_delta_time_ms) < timestamp <= ingame_time:
                        player_inputs_this_frame.extend(inputs)

            # Simulate next frame
            world_state.process_frame(player_inputs_this_frame, ingame_time)

            # Render this frame (new vfx_and_sfx_system not yet in use)
            rendering_framework.begin_frame()
            for spell_id in world_state.get_spell_ids_for_successful_events(ingame_time):
                OldIngameLoop._display_spell(rendering_framework, world_state, spell_id)
            game_objs_view: ValuesView[GameObj] = world_state.view_game_objs
            for game_obj in game_objs_view:
                OldIngameLoop._render_game_obj(rendering_framework, game_obj)
            OldIngameLoop._render_frame_actions(rendering_framework, ui_manager)
            rendering_framework.end_frame()

        # Cleanup when exiting game
        rendering_framework.terminate_rendering_framework()

    @staticmethod
    def _display_spell(rendering_framework: PygameRenderer, state: OldWorldState, spell_id: int) -> None:
        spell: Spell = state.spell_database.get_spell(spell_id)

        if spell.should_play_audio:
            rendering_framework.play_sound(spell.audio_name)

        if spell.should_play_animation:
            pos = (0.0, 0.0)  # Replace with real effect position later
            rendering_framework.play_animation(pos_xy=pos, scale=spell.animation_scale, asset_name=spell.animation_name)

    @staticmethod
    def _render_game_obj(rendering_framework: PygameRenderer, game_obj: GameObj) -> None:
        if game_obj.is_visible:
            x, y = game_obj.get_position_xy()
            rendering_framework.draw_blinking_circle(
                pos_xy=(x, y),
                scale=game_obj.size,
                color_rgb=game_obj.color,
                time_ms=rendering_framework.get_current_time(),
                asset_name=game_obj.sprite_name
            )

    @staticmethod
    def _render_frame_actions(rendering_framework: PygameRenderer, ui_manager: UiManager) -> None:
        for rend_act in ui_manager.get_render_actions():
            if rend_act.is_type_circle():
                scale = rend_act.convert_scale_xy_to_scale()
                rendering_framework.draw_circle(
                    rend_act.pos_xy,
                    scale,
                    rend_act.color_rgb,
                    rend_act.asset_name
                )

            elif rend_act.is_type_rectangle():
                rendering_framework.draw_rectangle(
                    rend_act.pos_xy,
                    rend_act.scale_xy,
                    rend_act.color_rgb,
                    rend_act.asset_name
                )

            elif rend_act.is_type_animation():
                scale = rend_act.convert_scale_xy_to_scale()
                rendering_framework.play_animation(
                    rend_act.pos_xy,
                    scale,
                    rend_act.asset_name
                )

            elif rend_act.is_type_text():
                font_size = rend_act.convert_scale_xy_to_font_size()
                rendering_framework.display_text(
                    rend_act.pos_xy,
                    font_size,
                    rend_act.color_rgb,
                    rend_act.text_to_display
                )

            elif rend_act.is_type_audio():
                rendering_framework.play_sound(rend_act.asset_name)

        ui_manager.clear_current_frame_event_cache()
